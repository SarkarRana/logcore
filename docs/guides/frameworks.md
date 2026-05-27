# Framework integration

LogCore is framework-agnostic, but here are drop-in patterns for the two most common Python web frameworks.

## Flask

```python
import uuid
from flask import Flask, request, g
from logcore import get_logger

app = Flask(__name__)
log = get_logger("webapp", json=True)


@app.before_request
def attach_correlation_id() -> None:
    g.correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))


@app.after_request
def log_response(response):
    with log.with_correlation_id(g.correlation_id):
        log.info(
            "request completed",
            method=request.method,
            path=request.path,
            status_code=response.status_code,
        )
    response.headers["X-Correlation-ID"] = g.correlation_id
    return response


@app.route("/users/<user_id>")
def get_user(user_id: str):
    with log.with_correlation_id(g.correlation_id):
        log.info("fetching user", user_id=user_id)
        # ... your handler logic ...
```

## FastAPI

```python
import time
import uuid
from fastapi import FastAPI, Request
from logcore import get_logger

app = FastAPI()
log = get_logger("api", json=True)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    cid = request.headers.get("x-correlation-id", str(uuid.uuid4()))
    started = time.perf_counter()

    with log.with_correlation_id(cid):
        log.info("request started", method=request.method, url=str(request.url))
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        log.info(
            "request completed",
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

    response.headers["x-correlation-id"] = cid
    return response
```

## ASGI middleware (generic)

For non-FastAPI ASGI apps (Starlette, Quart, etc.), use a standard ASGI middleware:

```python
import uuid
from logcore import get_logger, set_correlation_id

log = get_logger("api")


class CorrelationIDMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        headers = dict(scope.get("headers", []))
        cid = (
            headers.get(b"x-correlation-id", b"").decode()
            or str(uuid.uuid4())
        )
        set_correlation_id(cid)

        try:
            await self.app(scope, receive, send)
        finally:
            # Tail-based sampling cleanup — safe no-op if not using a sampler.
            log.flush_sample_buffer(cid)
```

```{tip}
The `flush_sample_buffer` call is only meaningful if you've attached a tail-based [sampler](sampling.md). It's a no-op otherwise, so leaving it in is safe.
```
