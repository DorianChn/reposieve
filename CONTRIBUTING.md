# Contributing to RepoSieve

Thanks for helping make AI-assisted development safer and less noisy.

## Local setup

RepoSieve has no runtime dependencies. Python 3.11 or newer is required.

```bash
python -m unittest discover -s tests -v
python -m reposieve scan . --json
```

## Pull requests

- Keep the free CLI useful without a paid account or hosted service.
- Add a regression test for bug fixes and new redaction patterns.
- Never add real credentials to fixtures, examples, or test output.
- Keep changes focused and document user-visible behavior.

For security-sensitive reports, use the private process in [`SECURITY.md`](SECURITY.md) instead of opening a public issue.
