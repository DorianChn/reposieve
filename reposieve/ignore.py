from __future__ import annotations

import fnmatch
from pathlib import PurePosixPath


DEFAULT_IGNORED_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".venv",
        "venv",
        "env",
        "node_modules",
        "__pycache__",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".tox",
        "dist",
        "build",
        "coverage",
        ".next",
        ".nuxt",
        "target",
        "vendor",
        ".idea",
        ".vscode",
    }
)

DEFAULT_IGNORED_EXTENSIONS = frozenset(
    {
        ".7z",
        ".avi",
        ".bin",
        ".bmp",
        ".class",
        ".dll",
        ".dmg",
        ".doc",
        ".docx",
        ".eot",
        ".exe",
        ".gif",
        ".ico",
        ".iso",
        ".jar",
        ".jpeg",
        ".jpg",
        ".lockb",
        ".mov",
        ".mp3",
        ".mp4",
        ".otf",
        ".pdf",
        ".pyc",
        ".so",
        ".sqlite",
        ".tar",
        ".ttf",
        ".wav",
        ".webm",
        ".webp",
        ".woff",
        ".woff2",
        ".xls",
        ".xlsx",
        ".zip",
    }
)


def load_gitignore_rules(root) -> list[str]:
    path = root / ".gitignore"
    if not path.is_file():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []
    return [line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#")]


def is_ignored(relative_path: str, rules: list[str] | tuple[str, ...]) -> bool:
    """Apply the useful, portable subset of gitignore matching rules."""

    path = _normalize_relative_path(relative_path)
    ignored = False
    for raw_rule in rules:
        rule = raw_rule.strip()
        if not rule:
            continue
        negated = rule.startswith("!")
        if negated:
            rule = rule[1:]
        if rule.endswith("/"):
            rule = rule.rstrip("/")
        if _matches(path, rule):
            ignored = not negated
    return ignored


def matches_pattern(relative_path: str, pattern: str) -> bool:
    """Return whether a relative path matches one include-style pattern."""

    pattern = pattern.strip()
    if not pattern or pattern.startswith("!"):
        return False
    return _matches(_normalize_relative_path(relative_path), pattern)


def _normalize_relative_path(relative_path: str) -> str:
    path = relative_path.replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    return path.lstrip("/")


def _matches(path: str, rule: str) -> bool:
    anchored = rule.startswith("/")
    rule = rule.lstrip("/")
    if not rule:
        return False

    path_obj = PurePosixPath(path)
    if "/" not in rule:
        return any(fnmatch.fnmatchcase(part, rule) for part in path_obj.parts)

    if fnmatch.fnmatchcase(path, rule) or path_obj.match(rule):
        return True
    if not anchored:
        return any(
            fnmatch.fnmatchcase("/".join(path_obj.parts[index:]), rule)
            for index in range(len(path_obj.parts))
        )
    return False
