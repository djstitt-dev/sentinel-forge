"""Offline CLI for creating or verifying Forge candidate manifests."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .package import CandidateManifest, FileIdentity, PackageError, build_manifest, verify_manifest

def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    b.add_argument("--root", required=True)
    b.add_argument("--revision", required=True)
    b.add_argument("--artifact-type", required=True)
    b.add_argument("--classification", required=True)
    b.add_argument("files", nargs="+")
    v = sub.add_parser("verify")
    v.add_argument("--root", required=True)
    v.add_argument("manifest")
    args = p.parse_args(argv)
    try:
        if args.command == "build":
            m = build_manifest(Path(args.root), args.files,
                work_package_revision=args.revision,
                artifact_type_class=args.artifact_type,
                classification_handling=args.classification)
            print(json.dumps(m.as_dict(), sort_keys=True, indent=2))
            return 0
        data = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        m = CandidateManifest(
            work_package_revision=data["work_package_revision"],
            artifact_type_class=data["artifact_type_class"],
            classification_handling=data["classification_handling"],
            source_component=data["source_component"],
            files=tuple(FileIdentity(**x) for x in data["files"]),
            artifact_id=data["artifact_id"],
            integrity_reference=data["integrity_reference"],
            integrity_provenance=data["integrity_provenance"],
            completeness_state=data["completeness_state"],
            format=data["format"],
        )
        ok = verify_manifest(Path(args.root), m)
        print(json.dumps({"verified": ok}, sort_keys=True))
        return 0 if ok else 1
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, PackageError) as exc:
        print(json.dumps({"verified": False, "error": str(exc)}, sort_keys=True))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
