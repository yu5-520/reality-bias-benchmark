import io
import json
import tarfile
import unittest

from arena.checkpoint_chronology import ChronologyError, ordered_checkpoints


def archive_for(objects):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as archive:
        for name, obj in objects.items():
            data = json.dumps(obj).encode()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    stream.seek(0)
    archive = tarfile.open(fileobj=stream)
    return archive, {m.name: m for m in archive.getmembers()}


def checkpoint(identity, event):
    return {"checkpoint_hash": identity, "event_ref": event,
            "application_file_hashes": {"app.py": identity}}


class FrozenChronologyTest(unittest.TestCase):
    def natural(self):
        # Hash order is intentionally the opposite of execution order.
        return {
            "checkpoints/zzz/manifest.json": checkpoint("zzz", "x2:task-start"),
            "checkpoints/aaa/manifest.json": checkpoint("aaa", "x2:terminal"),
            "checkpoint_ledger.json": {"checkpoints": [
                {"checkpoint_hash": "zzz", "event_ref": "x2:task-start", "model_decision_sequence": 0},
                {"checkpoint_hash": "aaa", "event_ref": "x2:terminal", "model_decision_sequence": 8},
            ]},
        }

    def test_ledger_beats_hash_order(self):
        archive, members = archive_for(self.natural())
        with archive:
            rows = ordered_checkpoints(archive, members)
        self.assertEqual([r[2]["checkpoint_hash"] for r in rows], ["zzz", "aaa"])
        self.assertEqual(rows[-1][2]["_chronology"]["sequence"], 8)

    def test_first_eligible_alias_does_not_create_an_event(self):
        data = self.natural()
        data["checkpoint_ledger.json"]["checkpoints"].append({
            "checkpoint_hash": "aaa", "event_ref": "struct:000012", "model_decision_sequence": 8})
        archive, members = archive_for(data)
        with archive:
            self.assertEqual(len(ordered_checkpoints(archive, members)), 2)

    def test_unbound_manifest_is_not_silently_sorted(self):
        data = self.natural()
        data["checkpoint_ledger.json"]["checkpoints"].pop()
        archive, members = archive_for(data)
        with archive, self.assertRaises(ChronologyError):
            ordered_checkpoints(archive, members)

    def test_ledger_clock_must_be_monotonic(self):
        data = self.natural()
        data["checkpoint_ledger.json"]["checkpoints"].reverse()
        archive, members = archive_for(data)
        with archive, self.assertRaises(ChronologyError):
            ordered_checkpoints(archive, members)

    def test_evidence_allowlist_still_applies(self):
        data = self.natural()
        archive, members = archive_for(data)
        with archive:
            rows = ordered_checkpoints(archive, members, allowed={"checkpoint_ledger.json", "checkpoints/zzz/manifest.json"})
        self.assertEqual(len(rows), 1)

    def test_legacy_b_uses_native_boundary_not_hash(self):
        data = {f"post_repair_checkpoints/{key}/manifest.json": checkpoint(key, event)
                for key, event in [("zzz", "host:turn:0002:post"), ("bbb", "host:turn:0010:post"), ("aaa", "host:terminal")]}
        archive, members = archive_for(data)
        with archive:
            rows = ordered_checkpoints(archive, members, "post_repair_checkpoints/")
        self.assertEqual([r[2]["checkpoint_hash"] for r in rows], ["zzz", "bbb", "aaa"])
        self.assertEqual(rows[-1][2]["_chronology"]["clock"], "native_turn")
        self.assertIsNone(rows[-1][2]["_chronology"]["sequence"])

    def test_unknown_or_tied_native_order_fails_closed(self):
        for events in [("opaque:1", "opaque:2"), ("host:terminal", "host:terminal")]:
            data = {f"post_repair_checkpoints/{key}/manifest.json": checkpoint(key, event)
                    for key, event in zip(("aaa", "bbb"), events)}
            archive, members = archive_for(data)
            with archive, self.assertRaises(ChronologyError):
                ordered_checkpoints(archive, members, "post_repair_checkpoints/")


if __name__ == "__main__":
    unittest.main()
