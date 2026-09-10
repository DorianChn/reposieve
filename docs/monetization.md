# RepoSieve product boundary

RepoSieve is intentionally designed as an open-core product. The free edition must be useful on its own; Pro should pay for convenience, collaboration, and distribution quality, not for basic privacy or the ability to run the scanner.

## Offer

| Edition | License | Price | Audience |
| --- | --- | ---: | --- |
| Community | MIT, free forever | $0 | Individual developers, students, open-source projects |
| Pro | Per-person lifetime license | Target $39 one-time | Developers and small teams that want review workflows and packaged UX |

There is no subscription, usage meter, hosted code upload, or required API account.

## Free boundary

The Community edition owns the trust-critical path:

- file discovery and `.gitignore` handling;
- deterministic ordering and token budgeting;
- common secret pattern detection;
- local redaction;
- Markdown/JSON export;
- CI exit codes and documentation.

Keeping these pieces public makes the security model inspectable and keeps the project useful if Pro is never purchased.

## Pro boundary

Pro can add a separately distributed package or binary for:

- local dashboard and interactive pack review;
- watch mode and multiple saved pack profiles;
- encrypted local history and visual diffs;
- team policy bundles and signed policy distribution;
- prebuilt binaries, release channels, and priority support.

Pro must preserve the same local-first default. Any optional network feature must be explicit, documented, and disabled by default.

## Launch sequence

1. Publish the Community MVP and collect feedback through GitHub Issues.
2. Add benchmark fixtures for precision, recall, scan speed, and pack usefulness.
3. Build a local Pro preview only after the CLI boundary is stable.
4. Add a real checkout and license delivery flow before accepting payment.
5. Publish a reproducible release checklist and a clear refund/support policy.

This repository currently implements step 1. The price is a product hypothesis, not a claim that checkout or Pro binaries are already available.
