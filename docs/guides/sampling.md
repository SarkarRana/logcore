# Log sampling

For high-throughput services, emitting every log record is wasteful. LogCore's `Sampler` combines three strategies in a single configurable object:

- **Level-aware** — records at levels in `always_keep` (default WARNING/ERROR/CRITICAL) are never sampled.
- **Tail-based** — when a correlation ID is set, records are buffered per request. The first record at an `always_keep` level retroactively flushes the buffer, capturing the full history of any failed request. If the request ends cleanly, the buffer is dropped.
- **Rate-based** — a fallback (`random.random() < rate`) used when tail-based is off or no correlation ID is present.

## When to use each strategy

| Need | Configuration |
|---|---|
| "I just want fewer logs" | `sample_rate=0.01` (or `Sampler(rate=0.01)`) |
| "Keep all errors, sample INFO/DEBUG" | `Sampler(rate=0.1)` (default `always_keep` does the right thing) |
| "Pay zero for healthy requests; keep everything when a request errors" | `Sampler(rate=0.0, tail_based=True)` |
| "Mix: sample healthy requests at 1%, keep failed ones in full" | `Sampler(rate=0.01, tail_based=True)` |

## Quickstart

```python
from logcore import get_logger, Sampler

log = get_logger(
    "api",
    sampler=Sampler(
        rate=0.01,                                    # 1% of INFO/DEBUG
        always_keep={"WARNING", "ERROR", "CRITICAL"}, # never sampled
        tail_based=True,                              # buffer per request
        tail_buffer_size=100,                         # max records per cid
    ),
)
```

Shortcut for rate-only sampling:

```python
log = get_logger("api", sample_rate=0.01)
```

## How tail-based works

```python
with log.with_correlation_id("req-abc"):
    log.info("received request")     # buffered (no error yet)
    log.info("validated input")      # buffered
    log.error("database timeout")    # flushes both INFOs + emits the error
    log.info("retrying")             # passes through (cid is now "interesting")
# On clean exit, any unflushed records are discarded silently.
```

Three things to note:

1. **Once a request errors, the cid stays in pass-through mode** for the rest of its life. Subsequent records emit directly. This is intentional — once a request is interesting, you want everything.
2. **The buffer is bounded.** `tail_buffer_size` records per correlation ID. When full, oldest is evicted (ring buffer). Eviction is counted in `stats().dropped_overflow`.
3. **Per-task isolation.** Buffers are keyed by correlation ID. Concurrent requests with different IDs are fully isolated.

## Using `set_correlation_id` instead of the context manager

If your middleware sets the correlation ID directly (no `with` block around the handler), you need to clean up the buffer manually at request end:

```python
from logcore import set_correlation_id

set_correlation_id(request.headers.get("x-correlation-id"))
# ... handle request ...
log.flush_sample_buffer()  # discard buffered records for the current cid
```

If you skip this and the request didn't error, the buffer leaks until process exit. (Errors flush the buffer themselves, so leaked buffers are only an issue for clean exits without explicit cleanup.)

## Environment variables

For deployments where you want to enable sampling without code changes:

```bash
LOGCORE_SAMPLE_RATE=0.01
LOGCORE_SAMPLE_TAIL=true
LOGCORE_SAMPLE_BUFFER_SIZE=100
LOGCORE_SAMPLE_ALWAYS_KEEP=WARNING,ERROR,CRITICAL
```

Setting any of these creates a `Sampler` automatically. Code-level `sampler=` argument always wins.

## Observability: `stats()`

```python
log.sampler.stats()
# SamplerStats(
#     active_buffers=3,         # cids currently buffering
#     buffered_records=42,      # total records sitting in buffers
#     dropped_overflow=0,       # records evicted from full buffers
#     kept=120,                 # records emitted directly
#     dropped=9500,             # records dropped by rate sampling
#     buffered=380,             # records ever entered the buffer (lifetime)
#     flushed=80,               # buffered records later emitted via error flush
#     discarded=258,            # buffered records dropped at clean exit
# )
```

Invariant: `buffered == flushed + discarded + buffered_records`.

Expose these as metrics via your usual stack (Prometheus, StatsD, etc.) to track sampling effectiveness.

## What's deliberately out of scope (for now)

- **Rate limiting** (records/sec cap) — see roadmap
- **Deterministic hashing** of correlation IDs for cross-service sampling
- **Per-call overrides** like `log.info("x", _sample_rate=0.001)`

These may land in a future release.

## See also

- [Correlation IDs](correlation_ids.md) — required for tail-based sampling to work
- {class}`~logcore.sampling.Sampler` — full API reference
