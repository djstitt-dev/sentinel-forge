"""Offline stdin/file validator for Sentinel Forge WP6 logical bundles."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .contract import ContractBundle

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an offline WP6 logical bundle")
    parser.add_argument("bundle", nargs="?", help="JSON bundle path; omit to read stdin")
    args = parser.parse_args(argv)
    try:
        raw = Path(args.bundle).read_text(encoding="utf-8") if args.bundle else sys.stdin.read()
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("top-level JSON value must be an object")
        result = ContractBundle(data).validate()
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"accepted": False, "issues": [{
            "code": "INPUT_ERROR", "path": "$", "message": str(exc)
        }]}, sort_keys=True))
        return 2
    print(json.dumps({
        "accepted": result.accepted,
        "issues": [
            {"code": x.code, "path": x.path, "message": x.message}
            for x in result.issues
        ],
    }, sort_keys=True))
    return 0 if result.accepted else 1

if __name__ == "__main__":
    raise SystemExit(main())
