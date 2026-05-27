# Sensitive data redaction

Every formatter in LogCore inherits from `RedactingFormatter`, which walks the log record and partially masks the values of fields whose names match a configurable set.

## Default protected fields

| Field name | Why |
|---|---|
| `password`, `passwd` | Authentication credentials |
| `secret` | Generic secret value |
| `token`, `api_key`, `access_token` | API credentials |
| `key`, `private_key` | Cryptographic keys |
| `auth`, `authorization` | Auth headers |
| `credential` | Generic credentials |
| `cert`, `certificate` | TLS material |

## What "partial masking" means

Values **≤ 4 characters** become `[REDACTED]` — there's no safe way to show a prefix without leaking the whole secret.

Values **longer than 4 characters** keep a 2-character prefix and replace the rest with `***`:

```python
log.info("auth", token="abc123-bearer-xyz", short="ab")
# Output: ... token=ab*** short=[REDACTED]
```

This is the right tradeoff for production logs: you can correlate two log lines that share a secret (e.g. trace the same API key across requests) without ever exposing the secret itself.

## Customizing

Add or replace the field set per-logger:

```python
log = get_logger(
    "vault",
    redact_fields={"password", "ssn", "credit_card", "api_token"},
)
```

Or via environment variable:

```bash
export LOGCORE_REDACT_FIELDS=password,ssn,credit_card
```

```{note}
The set you pass **replaces** the default — it doesn't extend it. If you want the defaults plus extras, include them explicitly: `redact_fields={"password", "token", ..., "ssn"}`.
```

## What gets walked

The redactor walks dict-typed values recursively. So nested data is covered:

```python
log.info("user", profile={"name": "alice", "password": "hunter2"})
# Output: ... profile={"name": "alice", "password": "hu***"}
```

But it does **not** scan free-form message strings. This is intentional — heuristic string scanning produces too many false positives. Pass sensitive values as fields, not as substrings of the message.

```python
# Good
log.info("login attempt", username=u, password=p)

# Bad — message string is NOT redacted
log.info(f"login attempt: user={u} pw={p}")
```
