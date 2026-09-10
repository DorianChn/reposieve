from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class SecretFinding:
    """A secret-like value without retaining the matched secret itself."""

    kind: str
    line: int


@dataclass(frozen=True)
class SkippedFile:
    path: str
    reason: str


@dataclass(frozen=True)
class ScannedFile:
    path: str
    absolute_path: Path
    size: int
    language: str
    content: str
    score: int
    findings: tuple[SecretFinding, ...] = field(default_factory=tuple)


@dataclass
class ScanResult:
    root: Path
    files: list[ScannedFile] = field(default_factory=list)
    skipped: list[SkippedFile] = field(default_factory=list)

    @property
    def findings(self) -> list[tuple[ScannedFile, SecretFinding]]:
        return [
            (file, finding)
            for file in self.files
            for finding in file.findings
        ]

    @property
    def total_bytes(self) -> int:
        return sum(file.size for file in self.files)
