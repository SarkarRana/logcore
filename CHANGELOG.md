# Changelog

All notable changes to LogCore are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.5] - 2026-05-20

### Fixed
- `TextFormatter` now applies the same partial-masking logic (`se***`) as `JSONFormatter` for redacted fields. Previously it emitted a flat `[REDACTED]` string, contradicting documented behavior.
- `TextFormatter` no longer emits stdlib `LogRecord` internals (`exc_info`, `exc_text`, `stack_info`, `taskName`) as extra key=value pairs on every line.
- `LogRecord.filename`, `lineno`, and `funcName` are now populated with the real call site instead of the hardcoded placeholder `"(unknown file)"` / `0`.
- `exc_info != True` guard in both formatters replaced with a plain truthiness check — the previous form was a no-op (a tuple is never `== True`) and could mask edge cases.

### Changed
- `skip_fields` de-duplicated into a single module-level `_STDLIB_LOG_FIELDS` frozenset shared by both `JSONFormatter` and `TextFormatter`. Adding a field to suppress now only requires one change.
- `get_logger` emits a `UserWarning` when called with configuration arguments for a name that already has a cached logger. Previously the replacement was silent, making it easy to create dangling references.

[0.1.5]: https://github.com/SarkarRana/logcore/compare/v0.1.4...v0.1.5

## [0.1.4] - 2025-01-15

### Added
- OpenTelemetry integration: `trace_id` and `span_id` are automatically injected into log records when an active span exists. Zero configuration required; install `logcore[otel]` to enable.
- `AsyncTimer` context manager for `async with logger.time(...)` in asyncio applications.
- `is_async_context()` utility to auto-detect running event loop.
- Partial masking for redacted fields: values longer than 4 characters show a short prefix (e.g. `se***`) instead of a blanket `[REDACTED]`, making it possible to correlate log lines without leaking secrets.
- `logcore/py.typed` marker for PEP 561 compliance.
- `examples/benchmark.py` with measured throughput numbers.

### Changed
- JSON formatter timestamps now emit UTC with timezone offset (`+00:00`) for unambiguous parsing by log aggregators.
- `is_async_context()` now uses `asyncio.get_running_loop()` (raises `RuntimeError` when no loop is running) instead of `asyncio.current_task()` (returned `None` in non-async contexts, making detection unreliable).
- `Optional[Set[str]]` type annotation used consistently across `LogCoreConfig`, `JSONFormatter`, and `TextFormatter` — removes false mypy errors under strict mode.
- Removed redundant `LogLevel.WARN` enum member; `LogLevel.from_string("WARN")` continues to normalise to `LogLevel.WARNING`.

### Fixed
- Logger caching lock now uses `threading.RLock` to prevent deadlocks when `get_logger` is called recursively from within a handler.

## [0.1.3] - 2024-12-01

### Changed
- Complete migration from `logforge` to `logcore` package name.
- Updated all internal references, classifiers, and PyPI metadata.

## [0.1.2] - 2024-11-15

### Added
- Environment variable configuration via `LOGCORE_*` prefix.
- `LOGCORE_REDACT_FIELDS` env var accepts a comma-separated list.
- File logging with `RotatingFileHandler`; configurable `max_file_size` and `backup_count`.
- `with_correlation_id()` context manager using `contextvars` for per-task isolation in async code.

### Changed
- `get_logger` returns a cached instance per name; passing configuration parameters forces a new instance.

## [0.1.1] - 2024-10-20

### Added
- `logger.time()` context manager that logs start, completion, and `duration_ms`.
- `logger.exception()` convenience method that captures the current traceback.
- Colorama-based coloured output in `TextFormatter`; falls back gracefully when colorama is absent.

## [0.1.0] - 2024-10-01

### Added
- Initial release as `logforge`.
- `get_logger(name)` single-entrypoint API.
- `JSONFormatter` and `TextFormatter`.
- `RedactingFormatter` base class with configurable sensitive-field redaction.
- Thread-safe logger registry.
- MIT license.

[0.1.4]: https://github.com/SarkarRana/logcore/compare/v0.1.3...v0.1.4
[0.1.3]: https://github.com/SarkarRana/logcore/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/SarkarRana/logcore/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/SarkarRana/logcore/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/SarkarRana/logcore/releases/tag/v0.1.0
