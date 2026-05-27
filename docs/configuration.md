# Configuration reference

All knobs are settable either as `get_logger(...)` keyword arguments or via environment variables. Code-level arguments always win.

## Core options

| Argument | Env var | Type | Default | Description |
|---|---|---|---|---|
| `level` | `LOGCORE_LEVEL` | `str` | `"INFO"` | One of `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. |
| `json` | `LOGCORE_JSON` | `bool` | `False` | `True` for structured JSON output; `False` for colored human-readable text. |
| `file` | `LOGCORE_FILE` | `str \| None` | `None` | Path to a log file. When set, a rotating file handler is added alongside the console handler. |
| `correlation_id` | `LOGCORE_CORRELATION_ID` | `str \| None` | `None` | Initial correlation ID set at logger creation. |
| `max_file_size` | `LOGCORE_MAX_FILE_SIZE` | `int` (bytes) | `10485760` (10 MB) | File rotation threshold. |
| `backup_count` | `LOGCORE_BACKUP_COUNT` | `int` | `5` | Number of rotated files to keep. |
| `redact_fields` | `LOGCORE_REDACT_FIELDS` | `set[str]` | See [redaction](guides/redaction.md) | Fields whose values are partially masked. |

## Sampling options

| Argument | Env var | Type | Default | Description |
|---|---|---|---|---|
| `sampler` | — | `Sampler \| None` | `None` | A fully constructed {class}`~logcore.sampling.Sampler` instance. |
| `sample_rate` | `LOGCORE_SAMPLE_RATE` | `float` | — | Shortcut: equivalent to `sampler=Sampler(rate=sample_rate)`. |
| — | `LOGCORE_SAMPLE_TAIL` | `bool` | `False` | Enable tail-based sampling via env var. |
| — | `LOGCORE_SAMPLE_BUFFER_SIZE` | `int` | `100` | Max records buffered per correlation_id. |
| — | `LOGCORE_SAMPLE_ALWAYS_KEEP` | `str` | `WARNING,ERROR,CRITICAL` | Comma-separated level names that are never sampled. |

```{important}
You can pass `sampler=` or `sample_rate=`, but not both — that raises `ValueError`. The env-var path constructs a single `Sampler` from any combination of the `LOGCORE_SAMPLE_*` vars.
```

## Boolean parsing for env vars

Env vars expecting booleans accept any of: `true`, `1`, `yes`, `on` (case-insensitive). Anything else is treated as `False`.

## Logger caching and reconfiguration

`get_logger(name)` returns a cached instance per name. Calling it again with **no** configuration arguments returns the same cached logger. Calling it with **any** configuration argument creates a new logger and replaces the cached one — and emits a `UserWarning`:

```text
UserWarning: Logger 'myapp' already exists and is being replaced with new
configuration. Existing references to the old logger will no longer receive
log records.
```

If you see this warning, you probably want to either configure the logger once at startup or use a different name for the second instance.

## Reading the current correlation ID without a logger

```python
from logcore import get_correlation_id, set_correlation_id

set_correlation_id("req-abc")
print(get_correlation_id())  # 'req-abc'
```

These work without instantiating a logger — useful for middleware that runs before any logger is created.
