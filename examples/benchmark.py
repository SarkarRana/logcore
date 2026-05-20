#!/usr/bin/env python3
"""Benchmark LogCore overhead vs stdlib logging."""

import logging
import os
import time

from logcore import get_logger
from logcore.logger import _loggers


def bench(fn, n: int = 20_000) -> float:
    """Return microseconds per call."""
    for _ in range(500):
        fn()
    start = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - start) / n * 1_000_000


def main() -> None:
    null = open(os.devnull, "w")

    # stdlib baseline
    stdlib_logger = logging.getLogger("bench_stdlib")
    stdlib_logger.handlers.clear()
    stdlib_logger.addHandler(logging.StreamHandler(null))
    stdlib_logger.setLevel(logging.INFO)

    # stdlib with JSON-like manual formatting
    class _JSONFmt(logging.Formatter):
        def format(self, r: logging.LogRecord) -> str:
            import json

            return json.dumps({"level": r.levelname, "msg": r.getMessage()})

    stdlib_json_logger = logging.getLogger("bench_stdlib_json")
    stdlib_json_logger.handlers.clear()
    h = logging.StreamHandler(null)
    h.setFormatter(_JSONFmt())
    stdlib_json_logger.addHandler(h)
    stdlib_json_logger.setLevel(logging.INFO)

    # logcore text
    _loggers.clear()
    lc_text = get_logger("bench_text", level="INFO", json=False)
    for hdlr in lc_text._logger.handlers:
        hdlr.stream = null  # type: ignore[attr-defined]

    # logcore json
    _loggers.clear()
    lc_json = get_logger("bench_json", level="INFO", json=True)
    for hdlr in lc_json._logger.handlers:
        hdlr.stream = null  # type: ignore[attr-defined]

    results = {
        "stdlib text": bench(lambda: stdlib_logger.info("benchmark message")),
        "stdlib JSON (manual)": bench(
            lambda: stdlib_json_logger.info("benchmark message")
        ),
        "logcore text": bench(lambda: lc_text.info("benchmark", user="alice", count=1)),
        "logcore JSON": bench(lambda: lc_json.info("benchmark", user="alice", count=1)),
    }

    print(f"\n{'Label':<26} {'µs/call':>10}  {'overhead vs stdlib':>20}")
    print("-" * 62)
    baseline = results["stdlib text"]
    for label, us in results.items():
        rel = f"+{us - baseline:.1f} µs" if us > baseline else "—"
        print(f"{label:<26} {us:>10.2f}  {rel:>20}")

    null.close()


if __name__ == "__main__":
    main()
