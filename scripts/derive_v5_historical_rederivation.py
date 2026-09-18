from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BINDING = ROOT / "configs/v5_historical_rederivation_source_binding_v0.1.json"
SPEC = ROOT / "configs/v5_historical_rederivation_spec_v0.1.json"

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()

def require(ok: bool, message: str):
    if not ok:
        raise SystemExit("FAIL: " + message)

def find_expected(obj, key):
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            found = find_expected(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for value in obj:
            found = find_expected(value, key)
            if found is not None:
                return found
    return None

def validate_sources() -> None:
    binding = load_json(BINDING)
    for src in binding["sources"]:
        path = ROOT / src["path"]
        require(path.exists(), f"missing source {src['path']}")
        raw = path.read_bytes()
        require(git_blob_sha(raw) == src["git_blob_sha"], f"blob sha drift: {src['path']}")
        body = raw.decode("utf-8")
        for token in src.get("required_tokens", []):
            require(token in body, f"missing token in {src['path']}: {token}")
        if src.get("expected_json"):
            obj = json.loads(body)
            for key, expected in src["expected_json"].items():
                actual = find_expected(obj, key)
                require(actual == expected, f"{src['path']} expected {key}={expected!r}, got {actual!r}")

def build_bundle():
    validate_sources()
    bundle = load_json(SPEC)
    require(bundle["summary"]["new_subject_model_calls"] == 0, "new subject calls must be zero")
    require(bundle["summary"]["new_evaluator_calls"] == 0, "new evaluator calls must be zero")
    require(bundle["summary"]["raw_evidence_mutated"] is False, "raw evidence mutation forbidden")
    return bundle

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out")
    p.add_argument("--check")
    args = p.parse_args()
    bundle = build_bundle()
    rendered = json.dumps(bundle, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        existing = Path(args.check).read_text(encoding="utf-8")
        require(existing == rendered, "checked-in re-derivation bundle differs from deterministic projection")
        print("PASS: checked-in v5 historical re-derivation bundle matches frozen-source projection")
        return
    require(args.out, "--out or --check is required")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(rendered, encoding="utf-8")
    print(f"WROTE={out}")
    print("NEW_SUBJECT_MODEL_CALLS=0")
    print("NEW_EVALUATOR_CALLS=0")

if __name__ == "__main__":
    main()
