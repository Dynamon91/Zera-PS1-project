#!/usr/bin/env python3
"""Check every file against a WIP checkpoint's embedded SHA-256 manifest."""
import argparse
import hashlib
import json
from pathlib import PurePosixPath
import zipfile


def verify_checkpoint(path):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("duplicate archive entries")
        status = json.loads(archive.read("zera_ps1/CHECKPOINT.json"))
        if status["schema_version"] != 1:
            raise ValueError("unsupported manifest schema")
        expected = {"zera_ps1/CHECKPOINT.json"}
        for name, info in status["files"].items():
            relative = PurePosixPath(name)
            if relative.is_absolute() or ".." in relative.parts or relative.as_posix() != name:
                raise ValueError("unsafe file path in manifest")
            member = "zera_ps1/" + name
            expected.add(member)
            data = archive.read(member)
            if len(data) != info["size"] or hashlib.sha256(data).hexdigest() != info["sha256"]:
                raise ValueError(f"file does not match checkpoint: {name}")
        if set(names) != expected:
            raise ValueError("archive contains unlisted or missing files")
    return status


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive")
    args = parser.parse_args()
    status = verify_checkpoint(args.archive)
    print(json.dumps({"verified_files": len(status["files"]),
                      "source_commit": status["source_commit"],
                      "checkpoint": status["checkpoint"],
                      "playable_build": status["playable_build"]}))


if __name__ == "__main__":
    main()
