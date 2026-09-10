from __future__ import annotations

import os
from pathlib import Path

from .config import Config
from .ignore import (
    DEFAULT_IGNORED_DIRS,
    DEFAULT_IGNORED_EXTENSIONS,
    is_ignored,
    load_gitignore_rules,
    matches_pattern,
)
from .models import ScanResult, ScannedFile, SkippedFile
from .redaction import find_secrets


LANGUAGE_BY_SUFFIX = {
    ".c": "C",
    ".cpp": "C++",
    ".cs": "C#",
    ".css": "CSS",
    ".go": "Go",
    ".html": "HTML",
    ".java": "Java",
    ".js": "JavaScript",
    ".json": "JSON",
    ".jsx": "JSX",
    ".kt": "Kotlin",
    ".md": "Markdown",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".sh": "Shell",
    ".sql": "SQL",
    ".swift": "Swift",
    ".toml": "TOML",
    ".ts": "TypeScript",
    ".tsx": "TSX",
    ".vue": "Vue",
    ".xml": "XML",
    ".yaml": "YAML",
    ".yml": "YAML",
}

IMPORTANT_FILES = {
    "readme": 120,
    "pyproject.toml": 115,
    "package.json": 115,
    "cargo.toml": 115,
    "go.mod": 115,
    "requirements.txt": 105,
    "dockerfile": 100,
    "makefile": 100,
    "license": 90,
    "contributing": 85,
    "security": 85,
    "agents.md": 110,
}


def scan_path(path: str | os.PathLike[str], config: Config | None = None) -> ScanResult:
    target = Path(path).expanduser()
    if not target.exists():
        raise FileNotFoundError(f"Path does not exist: {target}")
    if target.is_symlink():
        raise ValueError("Refusing to scan a symbolic link as the root path")

    config = config or Config()
    root = target if target.is_dir() else target.parent
    rules = [*load_gitignore_rules(root), *config.exclude]
    result = ScanResult(root=root.resolve())

    for candidate in _candidates(target, root, rules):
        relative = candidate.relative_to(root).as_posix()
        if config.include and not any(
            matches_pattern(relative, pattern) for pattern in config.include
        ):
            result.skipped.append(SkippedFile(relative, "not matched by include patterns"))
            continue
        if candidate.is_symlink():
            result.skipped.append(SkippedFile(relative, "symbolic link"))
            continue
        if candidate.suffix.lower() in DEFAULT_IGNORED_EXTENSIONS:
            result.skipped.append(SkippedFile(relative, "binary or generated extension"))
            continue
        try:
            size = candidate.stat().st_size
        except OSError as exc:
            result.skipped.append(SkippedFile(relative, f"stat failed: {exc}"))
            continue
        if size > config.max_file_bytes:
            result.skipped.append(SkippedFile(relative, "file exceeds max_file_bytes"))
            continue
        try:
            raw = candidate.read_bytes()
        except OSError as exc:
            result.skipped.append(SkippedFile(relative, f"read failed: {exc}"))
            continue
        if b"\x00" in raw:
            result.skipped.append(SkippedFile(relative, "binary content"))
            continue
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            result.skipped.append(SkippedFile(relative, "non-UTF-8 content"))
            continue
        findings = find_secrets(content)
        result.files.append(
            ScannedFile(
                path=relative,
                absolute_path=candidate,
                size=size,
                language=language_for(candidate),
                content=content,
                score=score_for(relative),
                findings=findings,
            )
        )

    result.files.sort(key=lambda file: file.path)
    result.skipped.sort(key=lambda file: file.path)
    return result


def _candidates(target: Path, root: Path, rules: list[str]):
    if target.is_file():
        relative = target.relative_to(root).as_posix()
        if not is_ignored(relative, rules):
            yield target
        return

    for current, directories, filenames in os.walk(target, topdown=True, followlinks=False):
        current_path = Path(current)
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in DEFAULT_IGNORED_DIRS
            and not is_ignored((current_path / directory).relative_to(root).as_posix(), rules)
        )
        for filename in sorted(filenames):
            candidate = current_path / filename
            relative = candidate.relative_to(root).as_posix()
            if not is_ignored(relative, rules):
                yield candidate


def language_for(path: Path) -> str:
    if path.name.lower() in {"dockerfile", "makefile", "procfile"}:
        return path.name.title()
    return LANGUAGE_BY_SUFFIX.get(path.suffix.lower(), "Text")


def score_for(relative_path: str) -> int:
    lower = relative_path.lower()
    basename = Path(lower).name
    for marker, score in IMPORTANT_FILES.items():
        if basename == marker or basename.startswith(marker + "."):
            return score
    if "/test" in lower or lower.startswith("test"):
        return 55
    if basename.endswith((".md", ".rst", ".txt")):
        return 75
    if basename.endswith((".py", ".ts", ".tsx", ".js", ".go", ".rs", ".java", ".rb")):
        return 65
    if basename.endswith((".lock", ".sum")):
        return 20
    return 45
