from __future__ import annotations

import re

from .models import SecretFinding


_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "private key",
        re.compile(
            r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?-----END [A-Z0-9 ]*PRIVATE KEY-----",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "GitHub token",
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    ),
    (
        "AWS access key",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    (
        "Slack token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    ),
    (
        "OpenAI-style API key",
        re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    ),
    (
        "npm token",
        re.compile(r"\bnpm_[A-Za-z0-9]{20,}\b"),
    ),
    (
        "Google API key",
        re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    ),
    (
        "JWT",
        re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"),
    ),
    (
        "generic secret assignment",
        re.compile(
            r"(?im)(?P<prefix>\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|passwd|secret|private[_-]?key)\b\s*[:=]\s*)(?P<quote>['\"]?)(?P<value>[A-Za-z0-9_./+=:@$-]{8,})(?P=quote)"
        ),
    ),
)


def find_secrets(text: str) -> tuple[SecretFinding, ...]:
    findings: set[tuple[str, int]] = set()
    for kind, pattern in _PATTERNS:
        for match in pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            findings.add((kind, line))
    return tuple(
        SecretFinding(kind=kind, line=line)
        for kind, line in sorted(findings, key=lambda item: (item[1], item[0]))
    )


def redact_secrets(text: str) -> tuple[str, tuple[SecretFinding, ...]]:
    findings = find_secrets(text)
    redacted = text
    for kind, pattern in _PATTERNS:
        replacement = f"[REDACTED: {kind}]"
        if kind == "generic secret assignment":
            redacted = pattern.sub(
                lambda match: f"{match.group('prefix')}{replacement}",
                redacted,
            )
        else:
            redacted = pattern.sub(replacement, redacted)
    return redacted, findings
