import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "research" / "tggates_rna_feedback_pilot_20261022"))
import rna_archive_acquire as acquire


FIXTURE_ROOT = ROOT / "log" / "20261022" / "tggates_rna_feedback_pilot" / "synthetic_tests"
FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)


class FakeResponse:
    def __init__(self, chunks, status=200):
        self.chunks = chunks
        self.status_code = status
        self.headers = {"Content-Length": str(sum(map(len, chunks)))}
        self.url = "https://fixture.invalid/archive.zip"

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def iter_content(self, chunk_size):
        return iter(self.chunks)


class FakeSession:
    def __init__(self, response):
        self.response = response

    def get(self, url, stream, timeout):
        if timeout != (10, 60) or stream is not True:
            raise AssertionError("unexpected request settings")
        return self.response


class ArchiveAcquireTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=FIXTURE_ROOT)
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_extracts_only_exact_whitelist_to_flat_directory(self):
        archive = self.root / "fixture.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("nested/003016012016.CEL", b"synthetic CEL bytes")
            zf.writestr("003016012017.CEL", b"another synthetic CEL")
            zf.writestr("003016012099.CEL", b"excluded synthetic member")
            zf.writestr("metadata/readme.txt", b"metadata")
        output = self.root / "flat"
        receipts = acquire.extract_selected(
            archive, {"003016012016.CEL", "003016012017.CEL"}, output)
        self.assertEqual({p.name for p in output.iterdir()},
                         {"003016012016.CEL", "003016012017.CEL"})
        self.assertEqual(len(receipts), 2)
        self.assertEqual((output / "003016012016.CEL").read_bytes(), b"synthetic CEL bytes")

    def test_rejects_duplicate_missing_and_unsafe_selected_members(self):
        duplicate = self.root / "duplicate.zip"
        with zipfile.ZipFile(duplicate, "w") as zf:
            zf.writestr("a/003016012016.CEL", b"one")
            zf.writestr("b/003016012016.CEL", b"two")
        with self.assertRaises(ValueError):
            acquire.extract_selected(duplicate, {"003016012016.CEL"}, self.root / "out1")
        missing = self.root / "missing.zip"
        with zipfile.ZipFile(missing, "w") as zf:
            zf.writestr("003016012016.CEL", b"one")
        with self.assertRaises(ValueError):
            acquire.extract_selected(missing, {"003016012016.CEL", "003016012017.CEL"}, self.root / "out2")
        self.assertRaises(ValueError, acquire.safe_member_basename, "../003016012016.CEL")
        self.assertRaises(ValueError, acquire.safe_member_basename, "folder\\003016012016.CEL")

    def test_short_download_keeps_partial_and_failure_receipt(self):
        archives, receipts = self.root / "archives", self.root / "receipts"
        job = {"compound_label": "fixture", "url": "https://fixture.invalid/archive.zip",
               "expected_bytes": 10, "allowed_basenames": set()}
        result = acquire.download_one(job, archives, receipts,
                                      FakeSession(FakeResponse([b"short", b"!"])))
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["actual_body_bytes"], 6)
        self.assertEqual(result["extra_body_bytes"], 0)
        self.assertTrue(Path(result["partial_archive"]).is_file())
        saved = json.loads(next(receipts.glob("*.json")).read_text(encoding="utf-8"))
        self.assertEqual(saved["error"], "body length mismatch: expected 10, received 6")
        self.assertFalse((archives / "fixture.zip").exists())

    def test_non_200_download_stops_and_records_status(self):
        archives, receipts = self.root / "archives_status", self.root / "receipts_status"
        job = {"compound_label": "fixture", "url": "https://fixture.invalid/archive.zip",
               "expected_bytes": 10, "allowed_basenames": set()}
        result = acquire.download_one(job, archives, receipts,
                                      FakeSession(FakeResponse([b"ignored"], status=206)))
        self.assertEqual(result["outcome"], "failed")
        self.assertEqual(result["status"], 206)
        self.assertEqual(result["actual_body_bytes"], 0)
        self.assertIn("unexpected HTTP status: 206", result["error"])
        self.assertFalse(list(archives.glob("*.part")))
        saved = json.loads(next(receipts.glob("*.json")).read_text(encoding="utf-8"))
        self.assertEqual(saved["status"], 206)

    def test_oversize_stream_stops_before_remaining_chunks(self):
        class Oversize(FakeResponse):
            def iter_content(self, chunk_size):
                yield b"12345678901"
                raise AssertionError("must not consume after excess")
        job = {"compound_label": "fixture", "url": "https://fixture.invalid/archive.zip",
               "expected_bytes": 10}
        result = acquire.download_one(job, self.root/'archives', self.root/'receipts',
                                      FakeSession(Oversize([])))
        self.assertEqual(result['actual_body_bytes'], 11)
        self.assertIn('stream stopped', result['error'])

    def test_member_receipts_enable_verified_reuse_but_reject_tampering(self):
        archive = self.root/'fixture.zip'
        with zipfile.ZipFile(archive, 'w') as zf:
            zf.writestr('001.CEL', b'first')
            zf.writestr('002.CEL', b'second')
        out, receipts = self.root/'out', self.root/'members'
        first = acquire.extract_selected(archive, {'001.CEL','002.CEL'}, out, receipts)
        self.assertEqual(len(list(receipts.glob('*.json'))), 2)
        second = acquire.extract_selected(archive, {'001.CEL','002.CEL'}, out, receipts)
        self.assertEqual(first, second)
        (out/'001.CEL').write_bytes(b'other')
        with self.assertRaises(ValueError):
            acquire.extract_selected(archive, {'001.CEL','002.CEL'}, out, receipts)

    def test_archive_must_match_authenticated_download_receipt(self):
        archive = self.root/'fixture.zip'
        archive.write_bytes(b'archive')
        receipts = self.root/'receipts'
        receipts.mkdir()
        job = dict(compound_label='fixture', url='https://fixture.invalid/archive.zip', expected_bytes=7)
        with self.assertRaises(ValueError):
            acquire.verify_archive(job, archive, receipts)
        acquire.write_receipt(receipts, 'fixture', dict(outcome='complete',status=200,
            url=job['url'],actual_body_bytes=7,sha256=acquire.sha256_file(archive)))
        self.assertEqual(acquire.verify_archive(job, archive, receipts), acquire.sha256_file(archive))
        archive.write_bytes(b'changed')
        with self.assertRaises(ValueError):
            acquire.verify_archive(job, archive, receipts)

    def test_freeze_pins_heads_and_script_hashes(self):
        _, jobs, manifest_sha = acquire.load_inputs()
        freeze_path = self.root / "freeze.json"
        freeze = {
            "status": acquire.AUTHORIZED_STATUS,
            "manifest_sha256": manifest_sha,
            "heads_sha256": acquire.sha256_file(acquire.HEADS),
            "script_sha256": acquire.sha256_file(Path(acquire.__file__)),
            "authorized_archive_count": len(jobs),
            "expected_archive_bytes": sum(job["expected_bytes"] for job in jobs),
        }
        freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
        self.assertEqual(acquire.check_freeze(freeze_path, manifest_sha, jobs)["status"],
                         acquire.AUTHORIZED_STATUS)
        freeze["heads_sha256"] = "0" * 64
        freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
        with self.assertRaises(ValueError):
            acquire.check_freeze(freeze_path, manifest_sha, jobs)

    def test_extraction_requires_its_own_directory_verification_freeze(self):
        _, _, manifest_sha = acquire.load_inputs()
        freeze_path = self.root / "extraction_freeze.json"
        freeze = {"status": "CEL_EXTRACTION_FROZEN_AND_AUTHORIZED",
                  "manifest_sha256": manifest_sha,
                  "heads_sha256": acquire.sha256_file(acquire.HEADS),
                  "script_sha256": acquire.sha256_file(Path(acquire.__file__)),
                  "selected_basename_rule_verified": True}
        freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
        self.assertEqual(acquire.check_extraction_freeze(freeze_path, manifest_sha)["status"],
                         "CEL_EXTRACTION_FROZEN_AND_AUTHORIZED")
        freeze["selected_basename_rule_verified"] = False
        freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
        with self.assertRaises(ValueError):
            acquire.check_extraction_freeze(freeze_path, manifest_sha)

    def test_archive_reuse_requires_size_and_matching_sha_receipt(self):
        archives, receipts = self.root / "archives_reuse", self.root / "receipts_reuse"
        archives.mkdir()
        receipts.mkdir()
        target = archives / "fixture.zip"
        target.write_bytes(b"0123456789")
        job = {"compound_label": "fixture", "url": "https://fixture.invalid/archive.zip",
               "expected_bytes": 10, "allowed_basenames": set()}
        saved = {"outcome": "complete", "status": 200, "actual_body_bytes": 10,
                 "sha256": acquire.sha256_file(target)}
        (receipts / "fixture_prior.json").write_text(json.dumps(saved), encoding="utf-8")
        self.assertEqual(acquire.download_one(job, archives, receipts)["outcome"], "reused_verified")
        target.write_bytes(b"short")
        with self.assertRaises(FileExistsError):
            acquire.download_one(job, archives, receipts)


if __name__ == "__main__":
    FIXTURE_ROOT.mkdir(parents=True, exist_ok=True)
    unittest.main()
