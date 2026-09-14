#!/usr/bin/env python3
import argparse, concurrent.futures, hashlib, json, threading
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from runners.run_r2_real import one_run, sha256_file

LOCK=threading.Lock()

def load_jsonl(path):
    return [json.loads(x) for x in Path(path).read_text(encoding="utf-8").splitlines() if x.strip()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--benchmark", default="benchmark/r2_primary_mapping_items_v0.3_calibration.jsonl")
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--max-workers", type=int, default=6)
    ap.add_argument("--out", required=True)
    args=ap.parse_args()

    config_path=ROOT/"configs/models/deepseek_r2_wave1.json"
    condition_path=ROOT/"conditions/r2_conditions_v0.3.json"
    benchmark_path=ROOT/args.benchmark

    config=json.loads(config_path.read_text(encoding="utf-8"))
    all_conditions=json.loads(condition_path.read_text(encoding="utf-8"))["conditions"]
    conditions={"baseline":all_conditions["baseline"]}
    items={x["item_id"]:x for x in load_jsonl(benchmark_path)}
    hashes={
        "model_config_hash":sha256_file(config_path),
        "conditions_hash":sha256_file(condition_path),
        "benchmark_hash":sha256_file(benchmark_path),
        "manifest_hash":hashlib.sha256(f"baseline|{args.repeats}|{benchmark_path.name}".encode()).hexdigest(),
    }
    manifest=[]
    for item in items.values():
        for trial in range(1,args.repeats+1):
            manifest.append({
                "wave":"R2-calibration-v0.3","item_id":item["item_id"],"bias":item["bias"],
                "authority":item["authority"],"trigger_strength":item.get("trigger_strength"),
                "condition":"baseline","trial":trial
            })

    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    if out.exists(): out.unlink()
    errors=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.max_workers) as ex, out.open("a",encoding="utf-8") as f:
        futs={ex.submit(one_run,e,config,conditions,items,hashes):e for e in manifest}
        for i,fut in enumerate(concurrent.futures.as_completed(futs),1):
            e=futs[fut]
            try:
                rec=fut.result()
                with LOCK:
                    f.write(json.dumps(rec,ensure_ascii=False)+"\n"); f.flush()
                print(f"[{i}/{len(manifest)}] OK {e['item_id']} t{e['trial']}")
            except Exception as err:
                errors.append({"entry":e,"error":repr(err)})
                print(f"[{i}/{len(manifest)}] ERROR {e}: {err}",file=sys.stderr)
    if errors:
        out.with_suffix(out.suffix+".errors.json").write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding="utf-8")
        raise SystemExit(f"{len(errors)} calibration runs failed")
    print(f"Completed {len(manifest)} calibration runs")

if __name__=="__main__":
    main()
