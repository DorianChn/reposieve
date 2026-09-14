from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path

from . import __version__
from .config import Config
from .packer import build_pack, result_as_json
from .scanner import scan_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reposieve",
        description="Inspect, redact, and pack repository context locally for AI coding agents.",
    )
    parser.add_argument("--version", action="version", version=f"RepoSieve {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="scan text files and report secret-like findings")
    scan.add_argument("path", nargs="?", default=".")
    scan.add_argument("--json", action="store_true", help="print machine-readable output")
    _add_filter_options(scan)

    check = subparsers.add_parser("check", help="fail when secret-like values are found")
    check.add_argument("path", nargs="?", default=".")
    check.add_argument("--json", action="store_true", help="print machine-readable output")
    _add_filter_options(check)

    pack = subparsers.add_parser("pack", help="create a budgeted Markdown or JSON context pack")
    pack.add_argument("path", nargs="?", default=".")
    pack.add_argument("--budget", type=int, help="approximate token budget; default 12000")
    pack.add_argument("--format", choices=("markdown", "json"), default="markdown")
    pack.add_argument("--output", "-o", type=Path, help="write the pack to a file")
    pack.add_argument(
        "--no-redact",
        action="store_true",
        help="disable secret redaction (use only for already-sanitized local data)",
    )
    _add_filter_options(pack)

    init = subparsers.add_parser("init", help="write a starter .reposieve.toml configuration")
    init.add_argument("path", nargs="?", default=".")
    init.add_argument("--force", action="store_true", help="replace an existing configuration")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "init":
        return _init_config(args.path, args.force)
    try:
        target = Path(args.path).expanduser()
        root = target if target.is_dir() else target.parent
        config = Config.from_root(root)
        overrides = {}
        if getattr(args, "budget", None) is not None:
            overrides["budget_tokens"] = args.budget
        if getattr(args, "max_file_bytes", None) is not None:
            overrides["max_file_bytes"] = args.max_file_bytes
        if getattr(args, "include", None):
            overrides["include"] = tuple(args.include)
        if getattr(args, "exclude", None):
            overrides["exclude"] = tuple(args.exclude)
        if getattr(args, "no_redact", False):
            overrides["redact"] = False
        if overrides:
            config = replace(config, **overrides)
        result = scan_path(target, config)
    except (FileNotFoundError, NotADirectoryError, PermissionError, ValueError) as exc:
        print(f"RepoSieve: {exc}", file=sys.stderr)
        return 2

    if args.command in {"scan", "check"}:
        payload = _scan_payload(result)
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            _print_scan(result)
        if args.command == "check" and result.findings:
            return 1
        return 0

    try:
        pack = build_pack(
            result,
            budget_tokens=config.budget_tokens,
            redact=config.redact,
        )
        output = result_as_json(result, pack) if args.format == "json" else pack.content
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
            print(
                f"Wrote {len(pack.included)} files ({pack.estimated_tokens:,} estimated tokens) to {args.output}",
                file=sys.stderr,
            )
        else:
            print(output, end="")
    except (OSError, ValueError) as exc:
        print(f"RepoSieve: {exc}", file=sys.stderr)
        return 2
    return 0


def _add_filter_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--include",
        action="append",
        metavar="PATTERN",
        help="only include matching paths; may be supplied more than once",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        metavar="PATTERN",
        help="exclude matching paths in addition to .gitignore",
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int,
        help="skip files larger than this size",
    )


def _init_config(path: str, force: bool) -> int:
    target = Path(path).expanduser()
    if not target.exists():
        print(f"RepoSieve: path does not exist: {target}", file=sys.stderr)
        return 2
    root = target if target.is_dir() else target.parent
    config_path = root / ".reposieve.toml"
    if config_path.exists() and not force:
        print(
            f"RepoSieve: {config_path} already exists; use --force to replace it",
            file=sys.stderr,
        )
        return 2
    template = (
        "[reposieve]\n"
        "budget_tokens = 12000\n"
        "max_file_bytes = 256000\n"
        "redact = true\n"
        "exclude = [\"context.md\"]\n"
    )
    try:
        config_path.write_text(template, encoding="utf-8")
    except OSError as exc:
        print(f"RepoSieve: could not write {config_path}: {exc}", file=sys.stderr)
        return 2
    print(f"Created {config_path}")
    return 0


def _scan_payload(result):
    return {
        # Keep machine-readable output portable and avoid exposing the local
        # user's absolute path when scan results are forwarded elsewhere.
        "root": ".",
        "files_scanned": len(result.files),
        "files_skipped": len(result.skipped),
        "total_bytes": result.total_bytes,
        "findings": [
            {"path": file.path, "kind": finding.kind, "line": finding.line}
            for file, finding in result.findings
        ],
        "skipped": [
            {"path": skipped.path, "reason": skipped.reason}
            for skipped in result.skipped
        ],
    }


def _print_scan(result) -> None:
    print(
        f"RepoSieve scanned {len(result.files)} text files "
        f"({result.total_bytes:,} bytes); skipped {len(result.skipped)}."
    )
    if not result.findings:
        print("No secret-like values detected.")
        return
    print("Potential secrets (values are never displayed):")
    for file, finding in result.findings:
        print(f"  - {file.path}:{finding.line} — {finding.kind}")
