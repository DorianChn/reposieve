from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Config:
    """Configuration loaded from .reposieve.toml plus safe defaults."""

    budget_tokens: int = 12_000
    max_file_bytes: int = 256_000
    redact: bool = True
    include: tuple[str, ...] = ()
    exclude: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.budget_tokens <= 0:
            raise ValueError("budget_tokens must be a positive integer")
        if self.max_file_bytes <= 0:
            raise ValueError("max_file_bytes must be a positive integer")
        if not isinstance(self.redact, bool):
            raise ValueError("redact must be true or false")

    @classmethod
    def from_root(cls, root: Path) -> "Config":
        config_path = root / ".reposieve.toml"
        if not config_path.is_file():
            return cls()

        try:
            import tomllib

            with config_path.open("rb") as handle:
                data: dict[str, Any] = tomllib.load(handle)
        except (OSError, ValueError) as exc:
            raise ValueError(f"Could not read {config_path.name}: {exc}") from exc

        values = data.get("reposieve", data)
        if not isinstance(values, dict):
            raise ValueError(".reposieve.toml must contain a [reposieve] table")

        budget = _positive_int(values.get("budget_tokens", cls.budget_tokens), "budget_tokens")
        max_file_bytes = _positive_int(
            values.get("max_file_bytes", cls.max_file_bytes),
            "max_file_bytes",
        )
        redact = values.get("redact", cls.redact)
        if not isinstance(redact, bool):
            raise ValueError("redact must be true or false")

        include = _string_tuple(values.get("include", ()), "include")
        exclude = _string_tuple(values.get("exclude", ()), "exclude")
        return cls(
            budget_tokens=budget,
            max_file_bytes=max_file_bytes,
            redact=redact,
            include=include,
            exclude=exclude,
        )


def _positive_int(value: Any, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _string_tuple(value: Any, name: str) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{name} must be a string or an array of strings")
    return tuple(value)
