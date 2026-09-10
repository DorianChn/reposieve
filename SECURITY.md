# Security policy

## Scope

RepoSieve is a local, pattern-based scanner and formatter. It does not contact a remote service during normal operation, but it should not be treated as a complete secret-management system.

## Safe defaults

- Secret-like values are never displayed in scan output.
- Context packs redact detected values by default.
- `.gitignore`, common generated directories, and binary extensions are skipped.
- No API key or telemetry is required.

## Limitations

Pattern scanners can miss unusual formats and can produce false positives. Always review a generated pack before sharing it with an AI tool or another person. Keep credentials in a proper secret manager and rotate credentials that may already have been committed.

## Reporting a vulnerability

Please do not publish an exploitable vulnerability or a real secret in a public issue. Open a private GitHub security advisory when the repository settings support it, or contact the maintainer through the GitHub profile associated with this repository. Include a minimal reproduction with synthetic values only.
