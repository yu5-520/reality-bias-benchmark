"""Verify frozen Stage-II runtime targets without claiming native-smoke success."""
import argparse, hashlib, importlib, json, subprocess
from pathlib import Path

BASE = Path(__file__).resolve().parent

def _head(path):
    return subprocess.check_output(["git","-C",str(path),"rev-parse","HEAD"], text=True).strip()

def _load():
    return json.loads((BASE/"runtime_bindings.json").read_text())

def _require_module(name):
    return importlib.import_module(name)

def check(probe, upstream=None, protocol_root=None):
    cfg=_load()["probes"][probe]
    if probe=="X5":
        raw=(BASE/"retrieval.py").read_bytes()
        if hashlib.sha256(raw).hexdigest()!=cfg["implementation_sha256"]:
            raise RuntimeError("X5 implementation hash mismatch")
        from .retrieval import retrieve
        hits=retrieve(BASE/"fixtures/project","checkout legacy current",limit=3)
        if not hits:
            raise RuntimeError("X5 retrieval returned no native hits")
        return {"probe":probe,"status":"RUNTIME_SURFACE_READY","detail":"in-repo retrieval executed"}
    if upstream is None:
        raise RuntimeError("upstream checkout required")
    upstream=Path(upstream)
    expected=cfg.get("sdk_commit") or cfg.get("source_commit")
    if _head(upstream)!=expected:
        raise RuntimeError(f"{probe} runtime checkout mismatch")
    if protocol_root:
        p=Path(protocol_root)
        if _head(p)!=cfg["protocol_commit"]:
            raise RuntimeError(f"{probe} protocol checkout mismatch")
    if probe=="X1":
        _require_module("autogen_core"); _require_module("autogen_agentchat")
    elif probe=="X2":
        _require_module("metagpt")
        schema=_require_module("metagpt.schema")
        if not hasattr(schema,"Message"): raise RuntimeError("MetaGPT Message missing")
    elif probe=="X3":
        _require_module("a2a")
    elif probe=="X4":
        _require_module("mcp")
    elif probe=="X6":
        for rel in cfg["required_paths"]:
            if not (upstream/rel).is_file(): raise RuntimeError(f"MemoryBank path missing: {rel}")
    elif probe=="X7":
        mod=_require_module("llmlingua")
        cls=getattr(mod,"PromptCompressor",None)
        if cls is None or not hasattr(cls,"compress_prompt"): raise RuntimeError("PromptCompressor.compress_prompt missing")
    else:
        raise RuntimeError("unknown probe")
    return {"probe":probe,"status":"RUNTIME_SURFACE_READY","detail":"frozen checkout and native API surface verified"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--probe",required=True,choices=[f"X{i}" for i in range(1,8)])
    p.add_argument("--upstream")
    p.add_argument("--protocol-root")
    a=p.parse_args()
    print(json.dumps(check(a.probe,a.upstream,a.protocol_root),sort_keys=True))

if __name__=="__main__":
    main()
