import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from package_wip import make_package, REQUIRED
from verify_checkpoint import verify_checkpoint


class PackageTests(unittest.TestCase):
    def test_resumable_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in REQUIRED:
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b'FILE "zera_wip08.bin" BINARY\n' if name.endswith(".cue") else name.encode())
            # Metadata from a previously unpacked checkpoint must be refreshed.
            (root / "CHECKPOINT.json").write_text("old metadata")
            for name in ("build/stale.exe", ".git/config", "tools/__pycache__/x.pyc"):
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text("excluded")
            output = root / "dist/checkpoint.zip"
            manifest = make_package(root, output, "a" * 40)
            before = output.read_bytes()
            make_package(root, output, "a" * 40)
            self.assertEqual(before, output.read_bytes())
            self.assertEqual(verify_checkpoint(output), manifest)
            with zipfile.ZipFile(output) as archive:
                self.assertIsNone(archive.testzip())
                saved = json.loads(archive.read("zera_ps1/CHECKPOINT.json"))
                self.assertEqual(saved, manifest)
                self.assertEqual(saved["playable_build"], "WIP08")
                self.assertFalse(saved["source_changes_in_disc"])
                self.assertEqual(set(saved["files"]), set(REQUIRED))
                self.assertEqual(len(archive.namelist()), len(REQUIRED) + 1)
                for name, info in saved["files"].items():
                    data = archive.read("zera_ps1/" + name)
                    self.assertEqual(len(data), info["size"])
                    self.assertEqual(hashlib.sha256(data).hexdigest(), info["sha256"])
            # Repack modified bytes with valid ZIP CRCs: SHA-256 must catch them.
            damaged = root / "dist/damaged.zip"
            with zipfile.ZipFile(output) as original, zipfile.ZipFile(damaged, "w") as changed:
                for name in original.namelist():
                    data = original.read(name)
                    changed.writestr(name, b"modified" if name.endswith("src/main.c") else data)
            with self.assertRaisesRegex(ValueError, "does not match checkpoint"):
                verify_checkpoint(damaged)
            native = root / "dist/native.zip"
            digest = hashlib.sha256(b"disc").hexdigest()
            check = {"bin_sha256": digest, "muted_rms": 0, "restored_rms": 20,
                     "source_commit": "b" * 40, "validation": "test fixture"}
            with zipfile.ZipFile(native, "w") as zipped:
                zipped.writestr("build/zera_wip09.bin", b"disc")
                zipped.writestr("build/zera.exe", b"PS-X EXE")
                zipped.writestr("build/zera_wip09.cue", 'FILE "zera_wip09.bin" BINARY')
                zipped.writestr("build/native-preview/capture.json", json.dumps({"bin_sha256": digest, "frames_run": 1600}))
                zipped.writestr("docs/screenshots/audio/verification.json", json.dumps(check))
            combined = root / "dist/combined.zip"
            make_package(root, combined, "a" * 40, native)
            combined_status = verify_checkpoint(combined)
            self.assertEqual(combined_status["additional_native_preview"]["source_commit"], "b" * 40)
            self.assertIn("native/Zera_PS1_WIP09_Native.zip", combined_status["files"])
            # Resuming an extracted WIP must replace its older nested build,
            # rather than emit two members with the same archive name.
            restored_native = root / "native/Zera_PS1_WIP09_Native.zip"
            restored_native.parent.mkdir()
            restored_native.write_bytes(b"older native archive")
            make_package(root, combined, "a" * 40, native)
            verify_checkpoint(combined)
            with zipfile.ZipFile(combined) as zipped:
                member = "zera_ps1/native/Zera_PS1_WIP09_Native.zip"
                self.assertEqual(zipped.namelist().count(member), 1)
                self.assertEqual(zipped.read(member), native.read_bytes())
            restored_native.write_bytes(native.read_bytes())
            make_package(root, combined, "a" * 40, restored_native)
            verify_checkpoint(combined)
            output.unlink()
            (root / "disc/zera_wip08.bin").unlink()
            with self.assertRaisesRegex(ValueError, "missing checkpoint file"):
                make_package(root, output, "a" * 40)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
