from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from reposieve.cli import _scan_payload
from reposieve.config import Config
from reposieve.packer import build_pack, result_as_json
from reposieve.redaction import find_secrets, redact_secrets
from reposieve.scanner import scan_path


class RedactionTests(unittest.TestCase):
    def test_detects_and_redacts_common_secret_shapes(self):
        aws_key = "AKIA" + "1234567890ABCDEF"
        github_token = "ghp_" + "123456789012345678901234567890"
        password = "super-" + "secret-value"
        npm_token = "npm_" + "123456789012345678901234567890"
        private_key_header = "-----BEGIN " + "PRIVATE KEY-----"
        private_key_footer = "-----END " + "PRIVATE KEY-----"
        text = (
            f"AWS={aws_key}\n"
            f"token={github_token}\n"
            f"password = '{password}'\n"
            f"npm={npm_token}\n"
            f"{private_key_header}\nprivate material\n{private_key_footer}\n"
        )

        findings = find_secrets(text)
        safe, safe_findings = redact_secrets(text)

        self.assertGreaterEqual(len(findings), 5)
        self.assertEqual(findings, safe_findings)
        self.assertNotIn(aws_key, safe)
        self.assertNotIn(github_token, safe)
        self.assertNotIn(npm_token, safe)
        self.assertNotIn(password, safe)
        self.assertNotIn("private material", safe)
        self.assertIn("[REDACTED", safe)


class ScannerTests(unittest.TestCase):
    def test_respects_gitignore_and_skips_binary_content(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".gitignore").write_text("ignored.txt\nsecret.env\n", encoding="utf-8")
            (root / "main.py").write_text("print('ok')\n", encoding="utf-8")
            (root / "ignored.txt").write_text("do not include\n", encoding="utf-8")
            (root / "secret.env").write_text("TOKEN=super-secret-value\n", encoding="utf-8")
            (root / "image.png").write_bytes(b"\x89PNG\r\n\x00binary")
            (root / ".git").mkdir()
            (root / ".git" / "config").write_text("internal", encoding="utf-8")

            result = scan_path(root)

            paths = {file.path for file in result.files}
            self.assertIn("main.py", paths)
            self.assertNotIn("ignored.txt", paths)
            self.assertNotIn("secret.env", paths)
            self.assertNotIn(".git/config", paths)
            self.assertIn("image.png", {file.path for file in result.skipped})

    def test_include_patterns_limit_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "app.py").write_text("pass", encoding="utf-8")
            (root / "notes.md").write_text("notes", encoding="utf-8")

            result = scan_path(root, Config(include=("*.py",)))

            self.assertEqual([file.path for file in result.files], ["app.py"])

    def test_cli_style_exclude_patterns_are_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "keep.py").write_text("pass", encoding="utf-8")
            (root / "generated.py").write_text("pass", encoding="utf-8")

            result = scan_path(root, Config(exclude=("generated.py",)))

            self.assertEqual([file.path for file in result.files], ["keep.py"])


class PackTests(unittest.TestCase):
    def test_pack_redacts_and_stays_near_budget(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("# Demo\n", encoding="utf-8")
            secret = "super-" + "secret-value"
            (root / "app.py").write_text(
                f"API_KEY={secret}\n" + "print('hello')\n" * 300,
                encoding="utf-8",
            )

            result = scan_path(root)
            pack = build_pack(result, budget_tokens=256)
            payload = json.loads(result_as_json(result, pack))

            self.assertNotIn(secret, pack.content)
            self.assertIn("README.md", pack.included)
            self.assertLessEqual(pack.estimated_tokens, 256)
            self.assertEqual(payload["estimated_tokens"], pack.estimated_tokens)
            self.assertEqual(payload["root"], ".")
            self.assertNotIn(str(root), result_as_json(result, pack))

    def test_scan_json_payload_does_not_expose_absolute_root(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "main.py").write_text("print('ok')\n", encoding="utf-8")

            payload = _scan_payload(scan_path(root))

            self.assertEqual(payload["root"], ".")
            self.assertNotIn(str(root), json.dumps(payload))

    def test_pack_budget_also_covers_a_large_repository_map(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(80):
                (root / f"module_{index:03d}.py").write_text("pass\n", encoding="utf-8")

            pack = build_pack(scan_path(root), budget_tokens=256)

            self.assertLessEqual(pack.estimated_tokens, 256)


if __name__ == "__main__":
    unittest.main()
