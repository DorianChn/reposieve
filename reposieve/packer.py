from __future__ import annotations

import json
import math
from dataclasses import dataclass

from .models import ScanResult, ScannedFile, SecretFinding
from .redaction import redact_secrets


@dataclass(frozen=True)
class PackResult:
    content: str
    included: tuple[str, ...]
    redactions: tuple[tuple[str, int], ...]
    estimated_tokens: int
    truncated: bool


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text) / 4) if text else 0


def build_pack(
    scan: ScanResult,
    budget_tokens: int,
    redact: bool = True,
) -> PackResult:
    if budget_tokens < 256:
        raise ValueError("budget_tokens must be at least 256")

    budget_chars = budget_tokens * 4
    files = sorted(scan.files, key=lambda file: (-file.score, file.path))
    prefix = _prefix(scan, files, budget_chars)
    chunks: list[str] = [prefix]
    included: list[str] = []
    redactions: list[tuple[str, int]] = []
    truncated = False
    used_chars = len(prefix)

    for file in files:
        safe_content, findings = redact_secrets(file.content) if redact else (
            file.content,
            file.findings,
        )
        section = _file_section(file, safe_content)
        if used_chars + len(section) <= budget_chars:
            chunks.append(section)
            used_chars += len(section)
            included.append(file.path)
            redactions.extend((finding.kind, finding.line) for finding in findings)
            continue

        remaining = budget_chars - used_chars
        header = f"\n\n## {file.path}\n\n```{_fence_language(file.language)}\n"
        footer = "\n```\n\n[truncated to stay within the token budget]\n"
        available = remaining - len(header) - len(footer)
        if available >= 80:
            chunks.append(header + safe_content[:available] + footer)
            included.append(file.path)
            redactions.extend((finding.kind, finding.line) for finding in findings)
            truncated = True
        break

    content = "".join(chunks)
    return PackResult(
        content=content,
        included=tuple(included),
        redactions=tuple(redactions),
        estimated_tokens=estimate_tokens(content),
        truncated=truncated,
    )


def result_as_json(scan: ScanResult, pack: PackResult) -> str:
    payload = {
        "root": str(scan.root),
        "files_scanned": len(scan.files),
        "files_skipped": len(scan.skipped),
        "files_included": list(pack.included),
        "estimated_tokens": pack.estimated_tokens,
        "redactions": [
            {"kind": kind, "line": line}
            for kind, line in pack.redactions
        ],
        "truncated": pack.truncated,
        "context": pack.content,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _prefix(scan: ScanResult, files: list[ScannedFile], budget_chars: int) -> str:
    intro = (
        "# Repository context\n\n"
        "> Generated locally by RepoSieve. Review the included files and any redaction markers before use.\n\n"
        f"## Repository map ({len(files)} text files)\n\n"
    )
    ending = "\n\n## Files\n"
    if not files:
        return (intro + "- _No text files found_" + ending)[:budget_chars]

    lines: list[str] = []
    used = len(intro) + len(ending)
    for file in files:
        line = f"- `{file.path}`\n"
        if used + len(line) > budget_chars:
            break
        lines.append(line)
        used += len(line)
    omitted = len(files) - len(lines)
    if omitted:
        marker = f"- _… {omitted} more files omitted from the map_\n"
        if used + len(marker) <= budget_chars:
            lines.append(marker)
    return (intro + ("".join(lines) or "- _Files omitted to stay within the budget_\n") + ending)[:budget_chars]


def _file_section(file: ScannedFile, content: str) -> str:
    return (
        f"\n\n## {file.path}\n\n"
        f"```{_fence_language(file.language)}\n"
        f"{content.rstrip()}\n"
        "```\n"
    )


def _fence_language(language: str) -> str:
    return {
        "C++": "cpp",
        "C#": "csharp",
        "JavaScript": "javascript",
        "Markdown": "markdown",
        "Python": "python",
        "TypeScript": "typescript",
        "YAML": "yaml",
    }.get(language, language.lower())
