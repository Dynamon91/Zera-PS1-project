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


def make_package(root, output, source_commit):
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
        "full_port_estimate_percent": 28,
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
                    if path.is_symlink():
                        raise ValueError(f"symlink is not supported: {relative}")
                    if path.suffix in {".pyc", ".pyo"}:
                        continue
                    data = path.read_bytes()
                    manifest["files"][relative] = {
                        "size": len(data), "sha256": hashlib.sha256(data).hexdigest()
                    }
                    write_entry(archive, relative, data)
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
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    output = args.output or root / "dist" / ARCHIVE_NAME
    manifest = make_package(root, output, args.source_commit)
    print(json.dumps({"archive": str(output), "files": len(manifest["files"]),
                      "checkpoint": CHECKPOINT, "playable_build": "WIP08"}))


if __name__ == "__main__":
    main()
