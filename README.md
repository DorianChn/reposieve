# RepoSieve

> Privacy-first repository context packs for AI coding agents.

**v0.5.0 · Beta Community edition · MIT**

RepoSieve turns a repository into a small, useful, reviewable context pack. It respects `.gitignore`, skips generated and binary files, detects common secret shapes, redacts them locally, and keeps the result inside a token budget.

No API key. No upload. No telemetry.

## Why this exists

AI coding agents are becoming a normal part of software development, but handing an entire repository to an agent is noisy and can expose credentials. RepoSieve is the small local boundary between a codebase and an AI tool: inspect first, redact by default, then pack only the files that fit.

## Quick start

```bash
# From a clone of this repository
python -m pip install .

# Inspect files and secret-like findings without showing secret values
reposieve scan .

# Use as a CI gate; exits 1 when a finding is present
reposieve check .

# Create a Markdown context pack for pasting into an AI coding tool
reposieve pack . --budget 12000 --output context.md

# Machine-readable output for scripts
reposieve pack . --format json --output context.json
```

JSON output uses `"root": "."` rather than exposing the caller's absolute local path.

The same commands work without installation:

```bash
python -m reposieve pack . --budget 8000
```

Create a starter configuration in any repository:

```bash
reposieve init .
```

## What the free Community edition includes

| Capability | Included |
| --- | :---: |
| Local repository scanning | Yes |
| `.gitignore` and generated-file filtering | Yes |
| Common secret detection and redaction | Yes |
| Markdown and JSON context packs | Yes |
| Approximate token budgeting | Yes |
| CI-friendly `check` command | Yes |
| API keys, cloud account, or telemetry | Never required |

The public Community edition is MIT-licensed and free forever.

## Pro, one-time purchase

RepoSieve Pro is planned as a lifetime, one-time license rather than a subscription. The target offer is **US$39 per person**, with no recurring fee and no requirement to send source code to a server.

Planned Pro value:

- local visual dashboard and drag-and-drop pack review;
- watch mode for continuously refreshed context packs;
- reusable team policy packs and repository-specific rules;
- encrypted local snapshots and side-by-side pack diffs;
- signed prebuilt binaries and priority support.

The checkout and Pro binaries are not claimed to be available yet. See [`docs/monetization.md`](docs/monetization.md) for the transparent product boundary and launch plan.

## Configuration

Create `.reposieve.toml` in the repository root:

```toml
[reposieve]
budget_tokens = 12000
max_file_bytes = 256000
redact = true
exclude = ["context.md", "docs/generated/"]
include = ["src/**", "README.md"]
```

Command-line options override the file configuration. Redaction is enabled by default. Use `--no-redact` only with content you have already reviewed locally.

You can also narrow a one-off pack without editing configuration:

```bash
reposieve pack . --include "src/**" --include "README.md" --exclude "src/generated/**"
```

## Security boundary

RepoSieve never prints matched secret values. It also does not retain the matched text in scan results. The scanner is intentionally conservative and pattern-based: a clean result is not proof that a repository contains no secrets. Read [`SECURITY.md`](SECURITY.md) before using it in a production workflow.

## Development

```bash
python -m unittest discover -s tests -v
python -m reposieve scan . --json
```

Contributions, issue reports, and new redaction test cases are welcome. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## More in this suite

AI agent security toolkit by DorianChn:

- [agent-canary](https://github.com/DorianChn/agent-canary) — zero-false-positive honeypot tripwires: decoy MCP tools + canary tokens
- [traceplay](https://github.com/DorianChn/traceplay) — record & replay agent trajectories in CI — zero tokens
- [agent-gate](https://github.com/DorianChn/agent-gate) — tool-call policy gateway: least privilege, short-lived credentials, audit
## License

MIT. See [`LICENSE`](LICENSE).
