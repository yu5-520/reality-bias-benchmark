from __future__ import annotations

import argparse
import json
from pathlib import Path

from .first_paper_analysis_contract import analyze_structural_comparisons, load_analysis_contract
from .io_utils import load_json, load_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--comparisons", required=True)
    parser.add_argument("--derivation-summary")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    comparisons = load_jsonl(args.comparisons)
    summary = load_json(args.derivation_summary) if args.derivation_summary else None
    contract = load_analysis_contract()
    analysis = analyze_structural_comparisons(
        comparisons,
        derivation_summary=summary,
        contract=contract,
    )

    out = Path(args.out)
    if out.exists():
        raise ValueError("refusing_to_overwrite_first_paper_analysis")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("FIRST_PAPER_R5MID_ANALYSIS=PASS")
    print(f"ANALYSIS_CONTRACT_HASH={analysis['analysis_contract_hash']}")
    print(f"PLANNED_PAIR_COUNT={analysis['planned_pair_count']}")
    print(f"COMPLETE_PAIR_COUNT={analysis['complete_pair_count']}")
    print(f"CENSORED_PAIR_COUNT={analysis['censored_pair_count']}")
    print(f"INTEGRITY_FAILURE_COUNT={analysis['integrity_failure_count']}")
    print(f"PRIMARY_INTERVAL_STATUS={analysis['primary_interval_status']}")
    print("PRIMARY_P_VALUE=NONE")
    print("SEMANTIC_STATUS=NOT_INCLUDED_IN_STRUCTURAL_ANALYSIS")
    print("PAID_API_CALLS=0")


if __name__ == "__main__":
    main()
