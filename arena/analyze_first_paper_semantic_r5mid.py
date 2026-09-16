from __future__ import annotations

import argparse
import json
from pathlib import Path

from .first_paper_semantic_analysis import analyze_semantic_reviews
from .io_utils import load_json, load_jsonl


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packets", required=True)
    parser.add_argument("--reviews", required=True)
    parser.add_argument("--derivation-summary")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    packets = load_jsonl(args.packets)
    reviews = load_jsonl(args.reviews)
    summary = load_json(args.derivation_summary) if args.derivation_summary else None
    analysis = analyze_semantic_reviews(
        packets,
        reviews,
        derivation_summary=summary,
    )

    out = Path(args.out)
    if out.exists():
        raise ValueError("refusing_to_overwrite_first_paper_semantic_analysis")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(analysis, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print("FIRST_PAPER_R5MID_SEMANTIC_ANALYSIS=PASS")
    print(f"PLANNED_PAIR_COUNT={analysis['planned_pair_count']}")
    print(f"RESOLVED_PAIR_COUNT={analysis['resolved_pair_count']}")
    print(f"UNRESOLVED_PAIR_COUNT={analysis['unresolved_pair_count']}")
    print(f"ESTIMATE_STATUS={analysis['authority_penetration']['estimate_status']}")
    print("PRIMARY_STRUCTURAL_ENDPOINT_UNCHANGED=YES")
    print("SOURCE_EVIDENCE_MUTATED=NO")
    print("PAID_EVALUATOR_CALLED=NO")


if __name__ == "__main__":
    main()
