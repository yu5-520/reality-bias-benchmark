"""Public, independently implemented field-bounded native application repair.

The full graph remains visible. Only a separately sealed branch policy grants
writes. This executor operates on a new application branch, never on an archive,
framework, historical message or model-private state. It makes no model call.
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from stage2.r7_checkpoint_v1.common import digest, file_tree_manifest
from stage2.native_v7.software_host_v1 import HostCheckout
from stage2.monitor_enhancement.snapshot_append import AppendOnlyEvidenceGraph

POLICY = "stage2-field-branch-policy-v1"
PLAN = "stage2-field-branch-plan-v1"


class BranchConstraintError(ValueError):
    pass


def require(condition, code):
    if not condition:
        raise BranchConstraintError(code)


def seal(row, key):
    value = copy.deepcopy(row)
    value[key] = digest(value)
    return value


def verify_seal(row, key):
    require(row.get(key) == digest({k: v for k, v in row.items() if k != key}), "SEAL_MISMATCH:" + key)


def exact_path(ref):
    require(isinstance(ref, str) and ref.startswith("file:"), "UNSUPPORTED_NATIVE_SURFACE")
    path = ref[5:]
    require(path and not Path(path).is_absolute() and ".." not in Path(path).parts
            and "\\" not in path and str(Path(path)) == path, "NONEXACT_PATH")
    require(not any(c in path for c in "*?[]"), "WILDCARD_PATH")
    return path


def pointer_parts(pointer):
    require(isinstance(pointer, str) and pointer.startswith("/") and pointer != "/", "EXACT_LEAF_POINTER_REQUIRED")
    parts = pointer[1:].split("/")
    for item in parts:
        # Reject invalid RFC 6901 escape spellings, rather than interpreting aliases.
        require(re.search(r"~(?![01])", item) is None, "INVALID_POINTER_ESCAPE")
    return [p.replace("~1", "/").replace("~0", "~") for p in parts]


def no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, "AMBIGUOUS_JSON_KEY")
        out[key] = value
    return out


def parse_json(text):
    return json.loads(text, object_pairs_hook=no_duplicates,
                      parse_constant=lambda value: (_ for _ in ()).throw(BranchConstraintError("NONFINITE_JSON")))


def leaf(document, pointer):
    parent = document
    parts = pointer_parts(pointer)
    for part in parts[:-1]:
        parent = parent[array_index(part)] if isinstance(parent, list) else parent[part]
    key = array_index(parts[-1]) if isinstance(parent, list) else parts[-1]
    value = parent[key]
    require(not isinstance(value, (dict, list)), "CONTAINER_REPLACEMENT_FORBIDDEN")
    return parent, key, value


def array_index(value):
    require(value == "0" or (value.isdigit() and not value.startswith("0")), "NONEXACT_ARRAY_INDEX")
    return int(value)


def transform(text, action, grant):
    """Only leaf replacement or one exact, nonempty UTF-8 text span."""
    kind = grant["kind"]
    require(action["kind"] == kind, "ACTION_KIND_DRIFT")
    if kind == "JSON_LEAF_REPLACE":
        require(action.get("pointer") == grant["pointer"], "FIELD_OUTSIDE_BRANCH")
        before = parse_json(text)
        after = copy.deepcopy(before)
        parent, key, old = leaf(after, grant["pointer"])
        require(digest(old) == action["before_value_hash"], "FIELD_PRECONDITION_MISMATCH")
        value = action["value"]
        require(not isinstance(value, (dict, list)), "CONTAINER_REPLACEMENT_FORBIDDEN")
        require(type(value) is type(old), "FIELD_TYPE_DRIFT")
        require(digest(value) != digest(old), "NO_EFFECT")
        parent[key] = value
        # Mask the one permitted leaf and verify all other JSON values unchanged.
        left = copy.deepcopy(before)
        right = copy.deepcopy(after)
        lp, lk, _ = leaf(left, grant["pointer"])
        rp, rk, _ = leaf(right, grant["pointer"])
        lp[lk] = rp[rk] = None
        require(left == right, "UNRELATED_JSON_FIELD_DRIFT")
        output = json.dumps(after, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        return output, {"field_path": grant["pointer"], "before_value_hash": digest(old),
                        "after_value_hash": digest(value), "preserve_measure": "ALL_OTHER_JSON_VALUES",
                        "formatting_preserved": False}
    require(kind == "TEXT_SPAN_REPLACE", "UNSUPPORTED_FIELD_OPERATION")
    start, end = grant["start"], grant["end"]
    require(type(start) is int and type(end) is int and 0 <= start < end <= len(text), "INVALID_TEXT_SPAN")
    require(action.get("start") == start and action.get("end") == end, "SPAN_OUTSIDE_BRANCH")
    old = text[start:end]
    require(digest(old.encode()) == grant["span_hash"] == action["before_value_hash"], "SPAN_PRECONDITION_MISMATCH")
    value = action["value"]
    require(isinstance(value, str) and value != old, "NO_EFFECT_OR_INVALID_TEXT")
    output = text[:start] + value + text[end:]
    require(output[:start] == text[:start] and output[start + len(value):] == text[end:], "UNRELATED_TEXT_DRIFT")
    return output, {"field_path": f"utf8-character-span:{start}:{end}",
                    "before_value_hash": digest(old.encode()), "after_value_hash": digest(value.encode()),
                    "preserve_measure": "EXACT_PREFIX_AND_SUFFIX_BYTES", "formatting_preserved": True}


def grant_identity(grant):
    return (grant["target_ref"], grant["kind"], grant.get("pointer"), grant.get("start"), grant.get("end"))


def select_grant(policy, action):
    matches = [g for g in policy["field_grants"] if grant_identity(g) == grant_identity(action)]
    require(len(matches) == 1, "FIELD_OUTSIDE_BRANCH_OR_AMBIGUOUS_GRANT")
    return matches[0]


def build_branch_policy(context, *, original_task, branch_id, route_refs, grants, evidence,
                        semantic_id, diagnosis_status="UNREVIEWED", mode="OFFLINE_NATIVE_FIXTURE"):
    """Host-side policy builder; never exposed as an agent mutation capability.

    A source locator proves source identity, not semantic adoption or truth.
    Only offline execution is currently supported, even for a reviewed diagnosis.
    """
    require(mode == "OFFLINE_NATIVE_FIXTURE", "LIVE_BRANCH_REPAIR_NOT_READY")
    require(branch_id and semantic_id and original_task, "BRANCH_BINDING_REQUIRED")
    visible = set(context.access.nodes)
    route = set(route_refs)
    require(route and route <= visible, "ROUTE_OUTSIDE_COMPLETE_GRAPH")
    require(grants, "FIELD_GRANTS_REQUIRED")
    require(evidence, "SOURCE_WITNESSES_REQUIRED")
    bound_evidence = []
    for source in evidence:
        locator = context.locator(source["member"])
        require(source["member_sha256"] == locator["member_sha256"], "SOURCE_WITNESS_DRIFT")
        bound_evidence.append(locator)
    bound = []
    seen, slots, kinds = set(), set(), {}
    for raw in grants:
        grant = copy.deepcopy(raw)
        ref = grant["target_ref"]
        exact_path(ref)
        require(ref in route, "GRANT_OUTSIDE_ROUTE")
        slot = grant_identity(grant)
        require(slot not in slots, "DUPLICATE_FIELD_GRANT")
        slots.add(slot)
        # Multiple disjoint JSON leaves are supported on the same object. A text
        # object has one exact span: later offsets cannot silently change meaning.
        if ref in kinds:
            require(kinds[ref] == grant["kind"] == "JSON_LEAF_REPLACE", "OVERLAPPING_OR_UNSUPPORTED_GRANTS")
        kinds[ref] = grant["kind"]
        seen.add(ref)
        current = context.read_file(ref)
        require(grant["kind"] in {"JSON_LEAF_REPLACE", "TEXT_SPAN_REPLACE"}, "UNSUPPORTED_FIELD_OPERATION")
        if grant["kind"] == "JSON_LEAF_REPLACE":
            _, _, old = leaf(parse_json(current["content"]), grant["pointer"])
            grant["before_value_hash"] = digest(old)
        else:
            start, end = grant["start"], grant["end"]
            require(type(start) is int and type(end) is int and 0 <= start < end <= len(current["content"]), "INVALID_TEXT_SPAN")
            grant["span_hash"] = digest(current["content"][start:end].encode())
            grant["before_value_hash"] = grant["span_hash"]
        grant["before_file_hash"] = current["source_locator"]["member_sha256"]
        grant["source_locator"] = current["source_locator"]
        bound.append(grant)
    return seal({"schema": POLICY, "branch_id": branch_id, "semantic_id": semantic_id,
                 "mode": mode, "original_task": copy.deepcopy(original_task),
                 "graph_hash": context.graph["graph_hash"], "archive_sha256": context.case["archive_sha256"],
                 "parent_checkpoint_hash": context.case["terminal_checkpoint_hash"],
                 "route_refs": sorted(route), "field_grants": bound,
                 "source_witnesses": bound_evidence, "diagnosis_status": diagnosis_status,
                 "semantic_adoption_verified": False,
                 "original_task_scope_narrowed": False, "history_immutable": True,
                 "native_surface": "EXPERIMENT_OWNED_APPLICATION_VIA_HostCheckout.write_file",
                 "unrelated_application_manifest": {
                     path: sha for path, sha in context.files_by_checkpoint[context.case["terminal_checkpoint_hash"]].items()
                     if "file:" + path not in seen}}, "policy_hash")


def compile_branch_plan(context, policy, actions, *, preserve_refs=(), verify_refs=(), route_relations=()):
    verify_seal(policy, "policy_hash")
    require(policy["schema"] == POLICY and policy["graph_hash"] == context.graph["graph_hash"], "POLICY_BINDING_MISMATCH")
    require(policy["parent_checkpoint_hash"] == context.case["terminal_checkpoint_hash"]
            and policy["archive_sha256"] == context.case["archive_sha256"], "PARENT_BINDING_MISMATCH")
    require(policy["mode"] == "OFFLINE_NATIVE_FIXTURE", "LIVE_BRANCH_REPAIR_NOT_READY")
    granted_refs = {x["target_ref"] for x in policy["field_grants"]}
    visible = set(context.access.nodes)
    require(set(preserve_refs) <= visible and set(verify_refs) <= visible, "PLAN_REF_OUTSIDE_GRAPH")
    require(not (set(preserve_refs) & granted_refs), "PRESERVE_WRITE_CONFLICT")
    require(not (set(verify_refs) & granted_refs), "UNVERIFIED_MUTATION_FORBIDDEN")
    compiled, completed, targets, used_slots, projected, last_action = [], set(), set(), set(), {}, {}
    require(actions, "COORDINATED_ACTIONS_REQUIRED")
    for raw in actions:
        action = copy.deepcopy(raw)
        ref, action_id = action["target_ref"], action["action_id"]
        require(ref in granted_refs, "WRITE_OUTSIDE_POLICY")
        require(action["kind"] in {g["kind"] for g in policy["field_grants"] if g["target_ref"] == ref}, "ACTION_KIND_DRIFT")
        grant = select_grant(policy, action)
        slot = grant_identity(grant)
        require(slot not in used_slots, "DUPLICATE_FIELD_ACTION")
        require(isinstance(action_id, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,80}", action_id), "NONEXACT_ACTION_ID")
        require(action_id not in completed, "DUPLICATE_ACTION_ID")
        require(set(action.get("depends_on", [])) <= completed, "UNSATISFIED_OR_CYCLIC_DEPENDENCY")
        require(action.get("reason"), "ACTION_REASON_REQUIRED")
        current = context.read_file(ref)["content"]
        require(digest(current.encode()) == grant["before_file_hash"], "SOURCE_VERSION_DRIFT")
        require(ref not in last_action or last_action[ref] in action.get("depends_on", []), "SAME_OBJECT_ORDER_REQUIRED")
        text = projected.get(ref, current)
        output, invariant = transform(text, action, grant)
        action.update(before_file_hash=digest(text.encode()), expected_output_hash=digest(output.encode()),
                      preserve_invariant=invariant)
        compiled.append(action)
        completed.add(action_id)
        targets.add(ref)
        used_slots.add(slot)
        projected[ref] = output
        last_action[ref] = action_id
    # Relationships remain claims unless their exact source witnesses are checked.
    relations = []
    witness_hashes = {x["member_sha256"] for x in policy["source_witnesses"]}
    for relation in route_relations:
        require(relation["source_ref"] in policy["route_refs"] and relation["destination_ref"] in policy["route_refs"], "RELATION_OUTSIDE_ROUTE")
        require(relation.get("status") in {"UNKNOWN", "CANDIDATE", "SOURCE_BOUND_CLAIM"}, "SEMANTIC_VERDICT_CANNOT_BE_ASSUMED")
        require(set(relation.get("witness_hashes", [])) <= witness_hashes, "RELATION_WITNESS_NOT_BOUND")
        relations.append(copy.deepcopy(relation))
    return seal({"schema": PLAN, "policy": copy.deepcopy(policy), "modify_refs": sorted(targets),
                 "preserve_refs": sorted(set(preserve_refs)), "verify_refs": sorted(set(verify_refs)),
                 "route_relations": relations, "actions": compiled,
                 "execution_order": [x["action_id"] for x in compiled],
                 "semantic_repair_effect": "NOT_EVALUATED", "live_provider_calls": 0}, "plan_hash")


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n")


class FullGraphBranchObserver:
    """Read-only before/during/after evidence capture; no native writes."""

    def __init__(self, graph, out, branch_id):
        self.out = Path(out)
        self.branch_id = branch_id
        self.before = copy.deepcopy(graph)
        self.graph = AppendOnlyEvidenceGraph.from_snapshot(graph)
        self.sequence = 0

    def capture(self, ref, content, phase, *, receipt=None, action_id=None, written=False):
        self.sequence += 1
        event = f"{self.branch_id}:field-repair:{self.sequence:06d}"
        path = self.out / "captures" / f"{self.sequence:06d}.json"
        raw = {"ref": ref, "content": content, "phase": phase, "action_id": action_id,
               "native_receipt": receipt, "provenance": "EXPERIMENT_ORIGIN_OFFLINE_NATIVE_FIXTURE"}
        save(path, raw)
        sha = digest(path.read_bytes())
        observation = {
            "schema": "RB-STAGE2-ENHANCED-OBSERVATION-v1", "event_ref": event,
            "trajectory_id": self.branch_id, "native_sequence": self.sequence,
            "clock_id": "offline_native_branch_capture", "event_kind": phase,
            "actor": "NATIVE_FIELD_EXECUTOR" if written else "EXTERNAL_READ_ONLY_OBSERVER",
            "evidence_ref": "evidence:" + sha, "object_refs": [ref],
            "written_refs": [ref] if written else [], "content_hash": digest(content.encode()),
            "field_path": (receipt or {}).get("field_path"), "version": digest(content.encode()),
            "visibility_scope": "OFFLINE_NATIVE_FIXTURE_NOT_NATURAL_TRAJECTORY",
            "source_locator": {"member": str(path.relative_to(self.out)), "member_sha256": sha,
                               "json_pointer": "/content", "line": None},
            "semantic_adoption_inferred": False,
        }
        self.graph.add_observation(observation)
        return observation

    def finish(self):
        after = self.graph.snapshot()
        old_observations = {x["observation_id"]: x for x in self.before["observations"]}
        new_observations = {x["observation_id"]: x for x in after["observations"]}
        old_edges = {x["edge_id"]: x for x in self.before["edges"]}
        new_edges = {x["edge_id"]: x for x in after["edges"]}
        require(all(new_observations.get(k) == v for k, v in old_observations.items()), "HISTORICAL_OBSERVATION_DRIFT")
        require(all(new_edges.get(k) == v for k, v in old_edges.items()), "HISTORICAL_RELATION_DRIFT")
        require({x["ref"] for x in self.before["nodes"]} <= {x["ref"] for x in after["nodes"]}, "FULL_GRAPH_NODE_LOSS")
        save(self.out / "full_graph_before.json", self.before)
        save(self.out / "full_graph_after.json", after)
        comparison = {"before_graph_hash": self.before["graph_hash"], "after_graph_hash": after["graph_hash"],
                      "before_nodes": len(self.before["nodes"]), "after_nodes": len(after["nodes"]),
                      "old_observations_preserved": len(old_observations), "old_edges_preserved": len(old_edges),
                      "new_observations": len(new_observations) - len(old_observations),
                      "historical_prefix_preserved": True, "semantic_repair_effect": "NOT_EVALUATED",
                      "captures_cover": "APPLICATION_BRANCH_BEFORE_DURING_AFTER_ONLY",
                      "native_agent_continuation_observed": False}
        save(self.out / "graph_comparison.json", comparison)
        return comparison


class NativeFieldBranchExecutor:
    """Restricted operation API: no shell, arbitrary write or policy-expansion API.

    Revalidate the whole plan before the first write. This is sequential version
    checking, not a concurrency-safe CAS or an OS-level lock. No concurrent agent
    runs in this offline branch. Failures keep partial execution and its evidence.
    """

    def __init__(self, context, plan, out, *, trusted_policy):
        verify_seal(plan, "plan_hash")
        policy = plan["policy"]
        # The host retains this policy separately. The agent cannot widen it by
        # editing and re-hashing the policy embedded in its proposed plan.
        require(policy == trusted_policy, "TRUSTED_POLICY_MISMATCH")
        verify_seal(policy, "policy_hash")
        # Recompile so a re-sealed tampered payload cannot bypass grant validation.
        recomputed = compile_branch_plan(context, policy, plan["actions"], preserve_refs=plan["preserve_refs"],
                                         verify_refs=plan["verify_refs"], route_relations=plan["route_relations"])
        require(recomputed == plan, "PLAN_RECOMPILE_MISMATCH")
        self.context, self.plan = context, copy.deepcopy(plan)
        self.out = Path(out)
        require(not self.out.exists(), "FRESH_BRANCH_REQUIRED")
        self.out.mkdir(parents=True)
        self.root = self.out / "application"
        self.root.mkdir()
        cp = context.case["terminal_checkpoint_hash"]
        self.original_manifest = copy.deepcopy(context.files_by_checkpoint[cp])
        for path, sha in self.original_manifest.items():
            target = self.root / exact_path("file:" + path)
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = context.raw("checkpoints/" + cp + "/application/" + path)
            require(digest(raw) == sha, "BRANCH_SOURCE_HASH_MISMATCH")
            target.write_bytes(raw)
        require(file_tree_manifest(self.root) == self.original_manifest, "NATIVE_BRANCH_COPY_DRIFT")
        self.checkout = HostCheckout(self.root)
        self.observer = FullGraphBranchObserver(context.graph, self.out, policy["branch_id"])
        self.executed = False
        save(self.out / "plan.json", self.plan)

    def execute(self, *, before_action=None):
        require(not self.executed, "BRANCH_ALREADY_EXECUTED")
        self.executed = True
        expected = copy.deepcopy(self.original_manifest)
        applied, receipts = [], []
        status, error = "PASS_OFFLINE_NATIVE_EXECUTION", None
        try:
            # Full branch preflight, including every preserved object, before writes.
            require(file_tree_manifest(self.root) == expected, "BRANCH_PREFLIGHT_VERSION_DRIFT")
            projected = {}
            for action in self.plan["actions"]:
                path = exact_path(action["target_ref"])
                text = projected.get(path, self.checkout.read_file(path))
                require(digest(text.encode()) == action["before_file_hash"], "PLAN_PREFLIGHT_VERSION_DRIFT")
                output, _ = transform(text, action, select_grant(self.plan["policy"], action))
                require(digest(output.encode()) == action["expected_output_hash"], "PLAN_OUTPUT_DRIFT")
                projected[path] = output
            for path in expected:
                self.observer.capture("file:" + path, self.checkout.read_file(path), "BRANCH_BEFORE")
            for action in self.plan["actions"]:
                if before_action is not None:
                    before_action(action, self.root)  # Offline failure injection, not an agent capability.
                require(set(action.get("depends_on", [])) <= set(applied), "DEPENDENCY_NOT_APPLIED")
                require(file_tree_manifest(self.root) == expected, "BRANCH_VERSION_OR_PRESERVE_DRIFT")
                ref, path = action["target_ref"], exact_path(action["target_ref"])
                before = self.checkout.read_file(path)
                require(digest(before.encode()) == action["before_file_hash"], "STALE_FIELD_VERSION")
                output, invariant = transform(before, action, select_grant(self.plan["policy"], action))
                require(digest(output.encode()) == action["expected_output_hash"], "PLAN_OUTPUT_DRIFT")
                self.observer.capture(ref, before, "ACTION_BEFORE", action_id=action["action_id"])
                save(self.out / "intents" / (action["action_id"] + ".json"),
                     {"target_ref": ref, "before_hash": digest(before.encode()), "expected_output_hash": action["expected_output_hash"]})
                native = self.checkout.write_file(path, output)
                # Record the attempt immediately, including a failed postcondition.
                observed = self.checkout.read_file(path)
                receipt = {"action_id": action["action_id"], "target_ref": ref,
                           "native_interface": "native:HostCheckout.write_file", "native_result": native,
                           "before_hash": digest(before.encode()), "after_hash": digest(observed.encode()),
                           "expected_output_hash": action["expected_output_hash"], **invariant}
                receipts.append(receipt)
                save(self.out / "native_action_receipts.json", receipts)
                self.observer.capture(ref, observed, "ACTION_AFTER", receipt=receipt,
                                      action_id=action["action_id"], written=True)
                require(observed == output, "NATIVE_POSTCONDITION_MISMATCH")
                expected[path] = digest(observed.encode())
                require(file_tree_manifest(self.root) == expected, "NATIVE_WRITE_SCOPE_DRIFT")
                applied.append(action["action_id"])
        except Exception as exc:
            status, error = "BLOCKED_WITH_PARTIAL_EVIDENCE", {"type": type(exc).__name__, "message": str(exc)}
        finally:
            for path in file_tree_manifest(self.root):
                self.observer.capture("file:" + path, self.checkout.read_file(path), "BRANCH_AFTER")
            comparison = self.observer.finish()
            manifest = file_tree_manifest(self.root)
            unrelated = self.plan["policy"]["unrelated_application_manifest"]
            # Include granted but unselected objects in the preservation check.
            unselected = {p: h for p, h in self.original_manifest.items() if "file:" + p not in self.plan["modify_refs"]}
            preserved = all(manifest.get(p) == h for p, h in {**unrelated, **unselected}.items())
            require(digest(Path(self.context.access.archive.name).read_bytes()) == self.context.case["archive_sha256"], "FROZEN_ARCHIVE_MUTATED")
            result = {"schema": "stage2-field-branch-execution-v1", "status": status, "error": error,
                      "plan_hash": self.plan["plan_hash"], "applied_action_ids": applied,
                      "native_write_attempts": len(receipts), "application_manifest": manifest,
                      "unrelated_application_preserved": preserved, "historical_archive_preserved": True,
                      "graph_comparison": comparison, "live_provider_calls": 0,
                      "semantic_repair_effect": "NOT_EVALUATED", "native_agent_continuation_executed": False,
                      "concurrent_writes_supported": False, "branch_promoted": False}
            save(self.out / "execution_receipt.json", result)
        return result
