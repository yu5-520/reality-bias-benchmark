"""Host entry connecting a revoked planning session to same-parent MCP repair.

Only offline engineering is enabled. Planning claims cannot invoke a provider,
choose verifier implementations, certify a repair exit or trigger paid review.
"""
import copy
from pathlib import Path

from stage2.route_repair.branch_fields import require, seal
from stage2.route_repair.mcp_same_parent import SameParentMCPBranch
from stage2.route_repair.planning_actor import ReadOnlyPlanningActorSession, _json


class OfflinePlanningRepairEntry:
    def __init__(self, planning, out):
        require(type(planning) is ReadOnlyPlanningActorSession, 'HOST_PLANNING_SESSION_REQUIRED')
        require(not planning._started, 'FRESH_HOST_PLANNING_SESSION_REQUIRED')
        self._planning = planning; self.out = Path(out); self._started = False
        require(not self.out.exists(), 'FRESH_PLANNING_ENTRY_REQUIRED')
        self.out.mkdir(parents=True)

    async def run(self, *, script=None, sdk_root=None, protocol_root=None, verifiers=None):
        require(not self._started, 'PLANNING_ENTRY_ALREADY_STARTED')
        self._started = True; planning_result = None; branch_result = None; failure = None
        try:
            planning_result = await self._planning.run()
            authorization = self._planning.authorization
            if planning_result['decision'] == 'REPAIR':
                require(authorization is not None, 'HOST_AUTHORIZATION_REQUIRED')
                branch = SameParentMCPBranch(authorization.context, authorization,
                    authorization.bundle, self.out / 'native_branch', script=script,
                    sdk_root=sdk_root, protocol_root=protocol_root, verifiers=verifiers or {})
                branch_result = await branch.run()
            else:
                require(authorization is None, 'NO_ACTION_DECISION_CANNOT_DISPATCH')
        except BaseException as exc:
            failure = {'error_type': type(exc).__name__, 'message': str(exc)}
            raise
        finally:
            if planning_result is None and self._planning._outcome is not None:
                planning_result = self._planning.outcome
            receipt = seal({'schema': 'stage2-offline-planning-repair-entry-v1',
                'state': 'FAILED' if failure else 'COMPLETED', 'failure': failure,
                'planning_outcome_hash': (planning_result or {}).get('outcome_hash'),
                'decision': (planning_result or {}).get('decision'),
                'native_branch_created': (self.out / 'native_branch').exists(),
                'native_branch_receipt': branch_result,
                'planning_exit_is_repair_exit': False, 'actual_repair_agent_exit': False,
                'provider_calls': 0, 'independent_review_invoked': False,
                'semantic_repair_effect': 'NOT_EVALUATED', 'repair_success': False,
                'automatic_replay_enabled': False, 'live_execution_enabled': False}, 'entry_hash')
            _json(self.out / 'entry_receipt.json', receipt)
        return copy.deepcopy(receipt)
