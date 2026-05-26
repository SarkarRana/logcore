"""Log sampling for LogCore.

Provides a single configurable ``Sampler`` that combines three strategies:

- **Level-aware**: records whose level name is in ``always_keep`` are never
  sampled. Defaults to ``{"WARNING", "ERROR", "CRITICAL"}``, which is
  equivalent to "never sample anything at or above WARNING".
- **Tail-based**: when a correlation_id is set, records are buffered; the
  first record whose level is in ``always_keep`` retroactively flushes the
  buffer (capturing the full request history) and switches the cid into
  pass-through mode. If the request ends cleanly without such a record, the
  buffer is discarded.
- **Rate-based**: a fallback used when tail-based is off or no correlation_id
  is present.

The buffer is bounded per correlation_id (ring buffer) so a misbehaving
request cannot consume unbounded memory.
"""

from __future__ import annotations

import os
import random
import threading
from collections import deque
from dataclasses import dataclass
from enum import Enum
from logging import LogRecord
from typing import Deque, Dict, FrozenSet, List, Optional, Set

from .utils import get_correlation_id

DEFAULT_ALWAYS_KEEP: FrozenSet[str] = frozenset({"WARNING", "ERROR", "CRITICAL"})
DEFAULT_TAIL_BUFFER_SIZE = 100


class Decision(Enum):
    """The action a Sampler decides to take for a given LogRecord."""

    KEEP = "keep"
    DROP = "drop"
    BUFFER = "buffer"


@dataclass
class SamplerStats:
    """Snapshot of sampler runtime state.

    Lifetime counters (since sampler creation):

    - ``kept``: records emitted directly (passed through sampling).
    - ``dropped``: records dropped by rate-based sampling.
    - ``buffered``: records that entered the tail-based buffer (regardless of
      eventual fate). ``buffered == flushed + discarded + buffered_records``.
    - ``flushed``: buffered records that were later emitted via an
      ``always_keep`` flush.
    - ``discarded``: buffered records that were dropped at clean request exit
      (no error fired).
    - ``dropped_overflow``: records evicted from a full buffer (ring-buffer
      overflow before flush/discard).

    Live state:

    - ``active_buffers``: number of correlation_ids currently buffering.
    - ``buffered_records``: total records currently sitting in buffers.
    """

    active_buffers: int
    buffered_records: int
    dropped_overflow: int
    kept: int
    dropped: int
    buffered: int
    flushed: int
    discarded: int


class Sampler:
    """Decides whether to emit, drop, or buffer log records.

    The full evaluation order inside :meth:`decide`:

    1. If ``record.levelname`` is in ``always_keep`` → ``KEEP``.
    2. If ``tail_based`` is on AND a correlation_id is set:
       - If the cid has already been flushed (an earlier error in this request
         drained the buffer) → ``KEEP`` (pass-through mode).
       - Otherwise → ``BUFFER``.
    3. Otherwise, a random draw against ``rate`` → ``KEEP`` or ``DROP``.

    The companion method :meth:`flush_pending` returns any buffered records
    that should be emitted alongside a kept ``always_keep`` record; the caller
    (LogCoreLogger) is expected to invoke it and emit those records before
    emitting the triggering record itself.

    Args:
        rate: Fraction of non-always-keep records to emit when rate-based
            sampling applies. Must be in [0.0, 1.0]. Defaults to 1.0 (keep all).
        always_keep: Level names that are never sampled. Defaults to
            {"WARNING", "ERROR", "CRITICAL"}.
        tail_based: When True, buffer records under the current correlation_id
            and flush on the first always_keep record. Defaults to False.
        tail_buffer_size: Max records buffered per correlation_id before the
            oldest is evicted. Defaults to 100.
        _rng: Optional ``random.Random`` for deterministic tests.
    """

    def __init__(
        self,
        rate: float = 1.0,
        always_keep: Optional[Set[str]] = None,
        tail_based: bool = False,
        tail_buffer_size: int = DEFAULT_TAIL_BUFFER_SIZE,
        _rng: Optional[random.Random] = None,
    ) -> None:
        if not 0.0 <= rate <= 1.0:
            raise ValueError(f"rate must be in [0.0, 1.0], got {rate}")
        if tail_buffer_size < 1:
            raise ValueError(f"tail_buffer_size must be >= 1, got {tail_buffer_size}")

        self.rate = rate
        # Normalize to uppercase so `always_keep={"warning"}` matches
        # `record.levelname == "WARNING"`. Without this, a lowercase entry
        # would silently never match — a sharp footgun.
        self.always_keep: FrozenSet[str] = (
            frozenset(level.upper() for level in always_keep)
            if always_keep is not None
            else DEFAULT_ALWAYS_KEEP
        )
        self.tail_based = tail_based
        self.tail_buffer_size = tail_buffer_size
        self._rng = _rng if _rng is not None else random.Random()

        self._buffers: Dict[str, Deque[LogRecord]] = {}
        self._flushed: Set[str] = set()
        self._lock = threading.Lock()
        self._stats: Dict[str, int] = {
            "kept": 0,
            "dropped": 0,
            "buffered": 0,
            "flushed": 0,
            "discarded": 0,
            "dropped_overflow": 0,
        }

    def decide(self, record: LogRecord) -> Decision:
        """Return the sampling decision for ``record``.

        Pure decision function — does not mutate the buffer. The caller is
        responsible for invoking :meth:`buffer` or :meth:`flush_pending` based
        on the returned decision.
        """
        if record.levelname in self.always_keep:
            return Decision.KEEP

        if not self.tail_based:
            if self.rate >= 1.0:
                return Decision.KEEP
            if self.rate <= 0.0:
                return Decision.DROP
            return Decision.KEEP if self._rng.random() < self.rate else Decision.DROP

        cid = get_correlation_id()
        if cid is None:
            if self.rate >= 1.0:
                return Decision.KEEP
            if self.rate <= 0.0:
                return Decision.DROP
            return Decision.KEEP if self._rng.random() < self.rate else Decision.DROP

        with self._lock:
            if cid in self._flushed:
                return Decision.KEEP
        return Decision.BUFFER

    def buffer(self, record: LogRecord) -> None:
        """Append ``record`` to the ring buffer for the current correlation_id.

        Silently does nothing if no correlation_id is set (defensive — the
        logger should only call this after :meth:`decide` returns BUFFER).
        Drops the oldest record if the buffer is full.
        """
        cid = get_correlation_id()
        if cid is None:
            return

        with self._lock:
            buf = self._buffers.get(cid)
            if buf is None:
                buf = deque(maxlen=self.tail_buffer_size)
                self._buffers[cid] = buf
            if len(buf) == self.tail_buffer_size:
                self._stats["dropped_overflow"] += 1
            buf.append(record)
            self._stats["buffered"] += 1

    def flush_pending(self, record: LogRecord) -> List[LogRecord]:
        """Return buffered records to emit alongside ``record``.

        Returns a non-empty list only when tail-based is on, the record's
        level is in ``always_keep``, and there are buffered records for the
        current correlation_id. Marks the cid as flushed so subsequent
        records pass through directly.
        """
        if not self.tail_based:
            return []
        if record.levelname not in self.always_keep:
            return []

        cid = get_correlation_id()
        if cid is None:
            return []

        with self._lock:
            buf = self._buffers.pop(cid, None)
            self._flushed.add(cid)
            if buf is None:
                return []
            records = list(buf)
            self._stats["flushed"] += len(records)
            return records

    def discard_buffer(self, correlation_id: str) -> int:
        """Drop the buffer for ``correlation_id`` without emitting.

        Called by :meth:`LogCoreLogger.with_correlation_id` on clean exit.
        Returns the number of records discarded. Safe to call when no buffer
        exists.
        """
        with self._lock:
            buf = self._buffers.pop(correlation_id, None)
            self._flushed.discard(correlation_id)
            n = len(buf) if buf is not None else 0
            self._stats["discarded"] += n
            return n

    def _record_kept(self) -> None:
        """Internal hook: increment the 'kept' stat (called by LogCoreLogger)."""
        with self._lock:
            self._stats["kept"] += 1

    def _record_dropped(self) -> None:
        """Internal hook: increment the 'dropped' stat (called by LogCoreLogger)."""
        with self._lock:
            self._stats["dropped"] += 1

    def stats(self) -> SamplerStats:
        """Return a snapshot of sampler counters and buffer state."""
        with self._lock:
            return SamplerStats(
                active_buffers=len(self._buffers),
                buffered_records=sum(len(b) for b in self._buffers.values()),
                dropped_overflow=self._stats["dropped_overflow"],
                kept=self._stats["kept"],
                dropped=self._stats["dropped"],
                buffered=self._stats["buffered"],
                flushed=self._stats["flushed"],
                discarded=self._stats["discarded"],
            )


def sampler_from_env() -> Optional[Sampler]:
    """Construct a Sampler from ``LOGCORE_SAMPLE_*`` env vars.

    Returns None if no sampling env vars are set. Recognises:

    - ``LOGCORE_SAMPLE_RATE`` — float in [0.0, 1.0]
    - ``LOGCORE_SAMPLE_TAIL`` — truthy enables tail-based
    - ``LOGCORE_SAMPLE_BUFFER_SIZE`` — int, max records per correlation_id
    - ``LOGCORE_SAMPLE_ALWAYS_KEEP`` — comma-separated level names
    """
    rate_env = os.getenv("LOGCORE_SAMPLE_RATE")
    tail_env = os.getenv("LOGCORE_SAMPLE_TAIL")
    buffer_env = os.getenv("LOGCORE_SAMPLE_BUFFER_SIZE")
    always_keep_env = os.getenv("LOGCORE_SAMPLE_ALWAYS_KEEP")

    if not any([rate_env, tail_env, buffer_env, always_keep_env]):
        return None

    kwargs: Dict[str, object] = {}
    if rate_env is not None:
        try:
            kwargs["rate"] = float(rate_env)
        except ValueError:
            pass
    if tail_env is not None:
        kwargs["tail_based"] = tail_env.lower() in ("true", "1", "yes", "on")
    if buffer_env is not None:
        try:
            kwargs["tail_buffer_size"] = int(buffer_env)
        except ValueError:
            pass
    if always_keep_env is not None:
        kwargs["always_keep"] = {
            level.strip().upper() for level in always_keep_env.split(",")
        }

    return Sampler(**kwargs)  # type: ignore[arg-type]
