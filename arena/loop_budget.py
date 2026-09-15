"""Runtime control for semantically blind R4 structural feedback budgets.

The counter itself lives in ``arena.structural_feedback``. This module only binds
an explicitly configured K condition to that frozen counter and decides when the
subject runtime must stop. It never reads semantic review fields.
"""
from .structural_feedback import VERSION as COUNTER_VERSION, derive_structural_feedback_rounds

RUNTIME_VERSION = 'R4-LOOP-BUDGET-RUNTIME-v0.1'
SUPPORTED_INITIAL_K = (2, 4)
TERMINATION_REASON = 'structural_feedback_round_limit_reached'
RUN_STATUS = 'LOOP_BUDGET_COMPLETE'


def validate_loop_budget_config(config):
    """Return normalized loop-budget settings or ``None`` for a Base run.

    Initial R4 policy authorizes only K=2 and K=4. A K condition must bind the
    exact counter version so a future counter revision cannot silently change an
    experimental arm.
    """
    if 'loop_budget' not in config and 'loop_budget_counter_version' not in config:
        return None

    k = config.get('loop_budget')
    if type(k) is not int or k not in SUPPORTED_INITIAL_K:
        raise ValueError(f'loop_budget must be one of {SUPPORTED_INITIAL_K}; got {k!r}')
    version = config.get('loop_budget_counter_version')
    if version != COUNTER_VERSION:
        raise ValueError(
            f'loop_budget_counter_version must be {COUNTER_VERSION}; got {version!r}'
        )
    if config.get('termination_policy') != 'observe_until_quiescent':
        raise ValueError('loop_budget requires termination_policy=observe_until_quiescent')
    return {
        'runtime_version': RUNTIME_VERSION,
        'counter_version': COUNTER_VERSION,
        'limit': k,
        'semantic_blind': True,
    }


def evaluate_loop_budget(run_id, events, model_calls, settings):
    """Derive the current neutral round count from contemporaneously recorded data."""
    if settings is None:
        return {
            'enabled': False,
            'runtime_version': RUNTIME_VERSION,
            'counter_version': COUNTER_VERSION,
            'limit': None,
            'round_count': 0,
            'reached': False,
            'reached_at_turn': None,
            'closing_event_ref': None,
            'round_ids': [],
        }

    result = derive_structural_feedback_rounds({
        'run_id': run_id,
        'events': events,
        'model_calls': model_calls,
        'observation_censored': False,
    })
    if result.get('counter_status') != 'RECORDED':
        raise RuntimeError('loop-budget counter unavailable for current runtime evidence')

    count = result['round_count']
    reached = count >= settings['limit']
    closing = None
    reached_turn = None
    if reached:
        boundary_round = result['rounds'][settings['limit'] - 1]
        closing = boundary_round['closing_event_ref']
        reached_turn = boundary_round['closing_turn']

    return {
        'enabled': True,
        'runtime_version': RUNTIME_VERSION,
        'counter_version': settings['counter_version'],
        'limit': settings['limit'],
        'round_count': count,
        'reached': reached,
        'reached_at_turn': reached_turn,
        'closing_event_ref': closing,
        'round_ids': [r['round_id'] for r in result['rounds']],
        'open_tail': result.get('open_tail'),
        'semantic_blind': True,
    }
