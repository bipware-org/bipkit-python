"""Regenerate strict Pydantic v2 models from spec/openapi.public.json using datamodel-code-generator."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "spec" / "openapi.public.json"
OUT = ROOT / "src" / "bipkit" / "types" / "generated.py"


def main() -> int:
    if not SPEC.exists():
        print(f"Missing OpenAPI spec at {SPEC}", file=sys.stderr)
        return 1
    cmd = [
        sys.executable,
        "-m",
        "datamodel_code_generator",
        "--input",
        str(SPEC),
        "--input-file-type",
        "openapi",
        "--output",
        str(OUT),
        "--output-model-type",
        "pydantic_v2.BaseModel",
        "--target-python-version",
        "3.10",
        "--use-standard-collections",
        "--use-union-operator",
    ]
    print("Running:", " ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
