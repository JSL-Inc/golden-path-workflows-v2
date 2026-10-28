import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

MODULE = Path(__file__).parents[1] / ".github/actions/artifactory-evidence/evidence.py"
spec = importlib.util.spec_from_file_location("evidence", MODULE)
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


class PackageContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "dist"
        self.source.mkdir()
        (self.source / "application.txt").write_text("built output")
        self.output = self.root / "evidence"
        self.sha = "a" * 40
        self.metadata = evidence.prepare(self.source, self.output, "app", "packages", self.sha, "123", "1")

    def test_tampered_package_rejected(self):
        with self.assertRaisesRegex(ValueError, "checksum"):
            evidence.verify(self.metadata, b"changed after build", "app", self.sha)

    def test_wrong_commit_rejected(self):
        with self.assertRaisesRegex(ValueError, "identity"):
            evidence.verify(self.metadata, (self.output / "package.tgz").read_bytes(), "app", "b" * 40)

    def test_wrong_application_rejected(self):
        with self.assertRaisesRegex(ValueError, "identity"):
            evidence.verify(self.metadata, (self.output / "package.tgz").read_bytes(), "another-app", self.sha)

    def test_empty_output_rejected(self):
        empty = self.root / "empty"
        empty.mkdir()
        with self.assertRaisesRegex(ValueError, "empty"):
            evidence.prepare(empty, self.output, "app", "packages", self.sha, "123", "1")

    def test_traversal_rejected(self):
        with self.assertRaises(ValueError):
            evidence.prepare(self.source, self.output, "../escape", "packages", self.sha, "123", "1")

    def test_symlink_rejected(self):
        (self.source / "link").symlink_to(self.output / "metadata.json")
        with self.assertRaisesRegex(ValueError, "Symlinks"):
            evidence.prepare(self.source, self.output, "app", "packages", self.sha, "123", "1")

    def test_output_inside_source_rejected(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            evidence.prepare(self.source, self.source / "evidence", "app", "packages", self.sha, "123", "1")

    def test_insecure_endpoint_rejected(self):
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            evidence.roundtrip(self.output, self.metadata, "http://example.invalid/artifactory", "secret")

    def test_transfer_contract_and_verification(self):
        storage = {}

        def fake_transfer(method, url, token, data=None):
            if method == "PUT":
                storage[url] = data
                return b""
            return storage[url]

        with patch.object(evidence, "transfer", side_effect=fake_transfer):
            evidence.roundtrip(self.output, self.metadata, "https://example.invalid/artifactory", "secret")
        self.assertEqual(json.loads((self.output / "retrieved/metadata.json").read_text()), self.metadata)

    def test_corrupt_download_rejected(self):
        def fake_transfer(method, url, token, data=None):
            if method == "PUT":
                return b""
            if url.endswith("metadata.json"):
                return json.dumps(self.metadata).encode()
            return b"corrupted"

        with patch.object(evidence, "transfer", side_effect=fake_transfer):
            with self.assertRaisesRegex(ValueError, "checksum"):
                evidence.roundtrip(self.output, self.metadata, "https://example.invalid/artifactory", "secret")


if __name__ == "__main__":
    unittest.main()
