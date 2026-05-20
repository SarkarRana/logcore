# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 0.1.x   | Yes       |

## Reporting a Vulnerability

Please **do not** open a public GitHub issue for security vulnerabilities.

Send a report to **rana.sarkar@ragnosticai.com** with:

- A description of the vulnerability and its potential impact
- Steps to reproduce or a minimal proof-of-concept
- The version(s) affected

You will receive an acknowledgement within 48 hours. If the issue is confirmed, a patched release will be published and you will be credited in the changelog unless you prefer to remain anonymous.

## Scope

Security issues most relevant to this library:

- **Redaction bypass**: a sensitive field that should be masked appearing in plaintext in log output
- **Log injection**: crafted input that corrupts the structure of JSON log records or injects extra fields
- **Dependency vulnerabilities**: issues in optional dependencies (`colorama`, `opentelemetry-api`)

Issues in example code or documentation that do not affect the library itself are out of scope for a CVE but are still welcome as regular bug reports.
