#!/usr/bin/env python3
"""Package a resumable source checkpoint without mislabeling its playable disc."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import zipfile

CHECKPOINT = "WIP09-source"
ARCHIVE_NAME = "Zera_PS1_WIP09_Source_Checkpoint.zip"
EXCLUDED_DIRS = {".git", "build", "dist", "__pycache__", ".pytest_cache", ".venv"}
REQUIRED = (
    "README.md", "PROGRESS.md", "src/main.c", "disc/zera.exe",
    "disc/zera.elf", "disc/zera.map", "disc/zera_wip08.bin", "disc/zera_wip08.cue",
)


def make_package(root, output, source_commit, native_artifact=None):
    root, output = Path(root).resolve(), Path(output).resolve()
    if not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        raise ValueError("source commit must be a full 40-character Git SHA")
    for name in REQUIRED:
        if not (root / name).is_file():
            raise ValueError(f"missing checkpoint file: {name}")
    cue = (root / "disc/zera_wip08.cue").read_text()
    if not re.search(r'FILE\s+"zera_wip08\.bin"\s+BINARY', cue, re.I):
        raise ValueError("CUE must reference the packaged WIP08 BIN")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    if output == root or output.is_dir():
        raise ValueError("output must name a ZIP file")

    manifest = {
        "schema_version": 1,
        "checkpoint": CHECKPOINT,
        "source_commit": source_commit,
        "playable_build": "WIP08",
        "source_changes_in_disc": False,
        "full_port_estimate_percent": 29,
        "estimate_basis": "Provisional weighted assessment in PROGRESS.md",
        "status": "New source is host-tested; bundled PS1 disc is the older WIP08 build.",
        "resume": "Use zera_ps1/ as the project root; read PROGRESS.md and README.md first.",
        "files": {},
    }

    def write_entry(archive, name, data):
        entry = zipfile.ZipInfo("zera_ps1/" + name, (2000, 1, 1, 0, 0, 0))
        entry.compress_type = zipfile.ZIP_DEFLATED
        entry.external_attr = 0o100644 << 16
        archive.writestr(entry, data, compresslevel=9)

    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            for base, directories, names in os.walk(root, followlinks=False):
                # Do not silently package files through directory symlinks.
                for directory in directories:
                    if directory not in EXCLUDED_DIRS and (Path(base) / directory).is_symlink():
                        raise ValueError("symlink directories are not supported")
                directories[:] = sorted(d for d in directories if d not in EXCLUDED_DIRS)
                for name in sorted(names):
                    path = Path(base) / name
                    relative = path.relative_to(root).as_posix()
                    if path in (output, temporary) or relative == "CHECKPOINT.json":
                        continue
                    # An extracted checkpoint already contains this nested ZIP.
                    # A supplied tested build replaces it once, below.
                    if native_artifact is not None and relative == "native/Zera_PS1_WIP09_Native.zip":
                        continue
                    if path.is_symlink():
                        raise ValueError(f"symlink is not supported: {relative}")
                    if path.suffix in {".pyc", ".pyo"}:
                        continue
                    data = path.read_bytes()
                    manifest["files"][relative] = {
                        "size": len(data), "sha256": hashlib.sha256(data).hexdigest()
                    }
                    write_entry(archive, relative, data)
            if native_artifact is not None:
                # Keep the tested native build separate from the older disc/ reference.
                data = Path(native_artifact).read_bytes()
                with zipfile.ZipFile(native_artifact) as native:
                    mascot = None
                    has_level3 = "docs/screenshots/level3/verification.json" in native.namelist()
                    if native.testzip() is not None:
                        raise ValueError("native artifact ZIP integrity failed")
                    check = json.loads(native.read("docs/screenshots/audio/verification.json"))
                    capture = json.loads(native.read("build/native-preview/capture.json"))
                    digest = hashlib.sha256(native.read("build/zera_wip09.bin")).hexdigest()
                    if check["bin_sha256"] != digest or capture["bin_sha256"] != digest:
                        raise ValueError("native artifact build/capture hashes disagree")
                    if capture["frames_run"] != 1600 or check["muted_rms"] >= 1 or check["restored_rms"] <= 10:
                        raise ValueError("native artifact validation evidence failed")
                    if "docs/screenshots/mascot/verification.json" in native.namelist():
                        mascot = json.loads(native.read("docs/screenshots/mascot/verification.json"))
                        if mascot["bin_sha256"] != digest or mascot["packed_vertices"] != 412 or mascot["animation_clips_observed"] != [0, 1, 2, 3] or mascot["automatic_respawns"] != 0:
                            raise ValueError("mascot build/animation validation mismatch")
                        if "camera_movement_aligned_samples" in mascot and (mascot["camera_movement_aligned_samples"] < 1 or mascot["blocked_idle_samples"] < 1):
                            raise ValueError("mascot motion validation failed")
                    if not native.read("build/zera.exe").startswith(b"PS-X EXE"):
                        raise ValueError("native artifact lacks a PS-X executable")
                    if '"zera_wip09.bin"' not in native.read("build/zera_wip09.cue").decode():
                        raise ValueError("native CUE does not reference the included BIN")
                name = "native/Zera_PS1_WIP09_Native.zip"
                manifest["files"][name] = {"size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                manifest["additional_native_preview"] = {
                    "archive": name, "source_commit": check["source_commit"],
                    "bin_sha256": digest, "validation": check["validation"],
                    "run": "Open build/zera_wip09.cue after extracting the native ZIP",
                }
                if mascot is not None:
                    manifest["additional_native_preview"]["mascot"] = {
                        "source_commit": mascot["source_commit"], "packed_vertices": mascot["packed_vertices"],
                        "textured_spot_faces": mascot["textured_spot_faces"], "textured_eye_faces": mascot["textured_eye_faces"],
                        "animation_clips_observed": mascot["animation_clips_observed"],
                    }
                if mascot is not None and "camera_movement_aligned_samples" in mascot:
                    manifest["additional_native_preview"]["mascot"]["camera_movement_aligned_samples"] = mascot["camera_movement_aligned_samples"]
                    manifest["additional_native_preview"]["mascot"]["blocked_idle_samples"] = mascot["blocked_idle_samples"]
                if has_level3:
                    with zipfile.ZipFile(native_artifact) as native:
                        level3 = json.loads(native.read("docs/screenshots/level3/verification.json"))
                        level3_hash = hashlib.sha256(native.read("build/zera_level3_preview.bin")).hexdigest()
                        if level3["bin_sha256"] != level3_hash or not level3["grounded"] or level3["automatic_respawns"] != 0:
                            raise ValueError("level3 preview build/validation mismatch")
                        if not native.read("build/zera_level3.exe").startswith(b"PS-X EXE"):
                            raise ValueError("level3 preview lacks a PS-X executable")
                        if '\"zera_level3_preview.bin\"' not in native.read("build/zera_level3_preview.cue").decode():
                            raise ValueError("level3 CUE does not reference included BIN")
                        manifest["additional_native_preview"]["level3_terrain_preview"] = {
                            "source_commit": level3["source_commit"], "bin_sha256": level3_hash,
                            "run": "Open build/zera_level3_preview.cue inside the same native ZIP",
                            "status": "Bounded original level3 terrain; no original progression active",
                        }
                write_entry(archive, name, data)
            write_entry(archive, "CHECKPOINT.json", (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
        # CRC check before replacing an existing output archive.
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP integrity check failed")
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--native-artifact", type=Path, help="Optional verified GitHub native artifact ZIP")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    output = args.output or root / "dist" / ARCHIVE_NAME
    manifest = make_package(root, output, args.source_commit, args.native_artifact)
    print(json.dumps({"archive": str(output), "files": len(manifest["files"]),
                      "checkpoint": CHECKPOINT, "playable_build": "WIP08"}))


if __name__ == "__main__":
    main()
