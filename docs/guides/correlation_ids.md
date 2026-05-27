# Correlation IDs

A **correlation ID** is a string that ties together log records from the same request, task, or workflow. LogCore stores the current ID in a `contextvars.ContextVar`, so it's automatically isolated per thread and per asyncio task — you set it once at the start of a request and every log call inside that scope picks it up.

## Three ways to set a correlation ID

### Context manager (recommended)

```python
from logcore import get_logger

log = get_logger("api")

with log.with_correlation_id("req-abc-123"):
    log.info("processing request")
    handle_request()
    log.info("done")
# Outside the block, the cid is unset again.
```

Pass no argument and LogCore generates a UUID for you:

```python
with log.with_correlation_id() as cid:
    log.info("starting work")
    response.headers["X-Correlation-ID"] = cid
```

### Bare setter (for middleware)

If you don't have a clean scope around your handler — e.g. you're in WSGI/ASGI middleware that sets the ID before the handler runs — use the standalone function:

```python
from logcore import set_correlation_id

set_correlation_id(request.headers.get("x-correlation-id"))
# Every subsequent log call in this task carries the cid.
```

```{important}
When you use `set_correlation_id` directly (not via the context manager) **and** you have a tail-based sampler attached, call `log.flush_sample_buffer()` at request end to clean up the per-cid buffer. See [sampling](sampling.md).
```

### At logger creation

For single-purpose scripts:

```python
log = get_logger("batch-job", correlation_id="nightly-2026-05-27")
```

## Reading the current correlation ID

```python
from logcore import get_correlation_id

cid = get_correlation_id()  # str or None
```

## Async safety

`contextvars` are isolated per asyncio task automatically — concurrent requests never bleed correlation IDs:

```python
import asyncio
from logcore import get_logger

log = get_logger("api")

async def handle(req_id: str) -> None:
    with log.with_correlation_id(req_id):
        log.info("start")
        await asyncio.sleep(0)
        log.info("done")

asyncio.run(asyncio.gather(handle("A"), handle("B"), handle("C")))
# A, B, C each see their own cid even though they run concurrently.
```

## Output

Correlation IDs appear in both output formats:

**JSON:**
```text
{"timestamp": "...", "level": "INFO", "message": "processing", "correlation_id": "req-abc-123", ...}
```

**Text:**
```
2026-05-27 10:30:45.123 INFO api [cid=req-abc-123]: processing
```

## See also

- [Framework integrations](frameworks.md) — Flask `before_request` and FastAPI middleware patterns
- [Sampling](sampling.md) — tail-based sampling uses correlation IDs as the per-request key
