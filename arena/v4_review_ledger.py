from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping

from .io_utils import load_jsonl
from .system_behavior import content_hash
from .v4_review_contract import validate_review_record
from .v4_review_packets import validate_review_packet


LEDGER_SUMMARY_SCHEMA = "RB-V4-REVIEW-LEDGER-IMPORT-SUMMARY-v0.1"


class V4ReviewLedgerError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise V4ReviewLedgerError(message)


def _packet_index(packets: Iterable[Mapping[str, Any]]) -> dict[str, Mapping[str, Any]]:
    out = {}
    for packet in packets:
        validate_review_packet(packet)
        packet_id = packet["packet_id"]
        _require(packet_id not in out, f"duplicate_v4_review_packet_id:{packet_id}")
        out[packet_id] = packet
    return out


def validate_review_ledger_records(
    packets: Iterable[Mapping[str, Any]],
    existing_records: Iterable[Mapping[str, Any]],
    new_records: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    packet_by_id = _packet_index(packets)
    existing = [dict(row) for row in existing_records]
    incoming = [dict(row) for row in new_records]
    all_ids = set()
    all_hashes = set()

    for row in existing:
        packet = packet_by_id.get(row.get("packet_id"))
        _require(packet is not None, f"existing_review_packet_missing:{row.get('packet_id')}")
        validate_review_record(row, packet=packet)
        record_id = row["review_record_id"]
        record_hash = row["record_hash"]
        _require(record_id not in all_ids, f"duplicate_existing_review_record_id:{record_id}")
        _require(record_hash not in all_hashes, f"duplicate_existing_review_record_hash:{record_hash}")
        all_ids.add(record_id)
        all_hashes.add(record_hash)

    incoming_ids = []
    for row in incoming:
        packet = packet_by_id.get(row.get("packet_id"))
        _require(packet is not None, f"new_review_packet_missing:{row.get('packet_id')}")
        validate_review_record(row, packet=packet)
        record_id = row["review_record_id"]
        record_hash = row["record_hash"]
        _require(record_id not in all_ids, f"review_record_id_already_exists:{record_id}")
        _require(record_hash not in all_hashes, f"review_record_hash_already_exists:{record_hash}")
        all_ids.add(record_id)
        all_hashes.add(record_hash)
        incoming_ids.append(record_id)

    available_parent_ids = set(all_ids)
    for row in incoming:
        for parent_id in row.get("parent_review_ids") or []:
            _require(parent_id != row["review_record_id"], "review_record_cannot_parent_itself")
            _require(parent_id in available_parent_ids, f"review_parent_record_missing:{parent_id}")
        if row.get("record_kind") in {"recheck", "adjudication"}:
            _require(bool(row.get("parent_review_ids")), f"{row['record_kind']}_requires_parent_review_ids")

    reviewer_packet_pairs = set()
    for row in [*existing, *incoming]:
        reviewer_id = (row.get("reviewer") or {}).get("id")
        key = (row.get("packet_id"), reviewer_id, row.get("record_kind"), row.get("review_record_id"))
        _require(key not in reviewer_packet_pairs, "duplicate_reviewer_packet_record_identity")
        reviewer_packet_pairs.add(key)

    return {
        "existing_record_count": len(existing),
        "incoming_record_count": len(incoming),
        "combined_record_count": len(existing) + len(incoming),
        "incoming_review_record_ids": incoming_ids,
        "packet_count": len(packet_by_id),
    }


def append_review_records(
    *,
    packets_path: str | Path,
    reviews_path: str | Path,
    ledger_path: str | Path,
    summary_path: str | Path | None = None,
) -> dict[str, Any]:
    packets_path = Path(packets_path)
    reviews_path = Path(reviews_path)
    ledger_path = Path(ledger_path)
    _require(packets_path.is_file(), "v4_review_packets_file_required")
    _require(reviews_path.is_file(), "v4_new_reviews_file_required")
    packets = load_jsonl(packets_path)
    incoming = load_jsonl(reviews_path)
    _require(incoming, "v4_review_import_requires_at_least_one_record")
    existing = load_jsonl(ledger_path) if ledger_path.exists() else []

    validated = validate_review_ledger_records(packets, existing, incoming)
    before_size = ledger_path.stat().st_size if ledger_path.exists() else 0
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as fh:
        for row in incoming:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    after_size = ledger_path.stat().st_size
    _require(after_size > before_size, "v4_review_ledger_append_did_not_grow")

    combined = load_jsonl(ledger_path)
    validate_review_ledger_records(packets, [], combined)
    summary = {
        "schema": LEDGER_SUMMARY_SCHEMA,
        "version": "0.1",
        "packets_file_sha256": __import__("arena.io_utils", fromlist=["sha256_file"]).sha256_file(packets_path),
        "incoming_reviews_file_sha256": __import__("arena.io_utils", fromlist=["sha256_file"]).sha256_file(reviews_path),
        "ledger_record_count_before": len(existing),
        "ledger_record_count_appended": len(incoming),
        "ledger_record_count_after": len(combined),
        "incoming_review_record_ids": validated["incoming_review_record_ids"],
        "source_evidence_mutated": False,
        "append_only": True,
        "automatic_paid_evaluator_called": False,
        "review_disagreement_preserved": True,
    }
    summary["summary_hash"] = content_hash(summary)
    if summary_path is not None:
        summary_path = Path(summary_path)
        _require(not summary_path.exists(), "refusing_to_overwrite_v4_review_import_summary")
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packets", required=True)
    parser.add_argument("--reviews", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--summary")
    args = parser.parse_args()
    summary = append_review_records(
        packets_path=args.packets,
        reviews_path=args.reviews,
        ledger_path=args.ledger,
        summary_path=args.summary,
    )
    print(
        f"V4_REVIEW_LEDGER_APPEND=PASS appended={summary['ledger_record_count_appended']} "
        f"total={summary['ledger_record_count_after']} paid_evaluator=NO source_evidence_mutated=NO"
    )


if __name__ == "__main__":
    main()
