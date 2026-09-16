import json


class BudgetExceeded(RuntimeError):
    pass


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def pricing_policy(model_config):
    provider = model_config.get('provider')
    if provider == 'deepseek':
        snap = model_config.get('pricing_snapshot_usd_per_million_tokens') or {}
        peak = snap.get('peak') or {}
        _require(all(k in peak for k in ('input_cache_hit', 'input_cache_miss', 'output')), 'deepseek_peak_pricing_required')
        return {
            'currency': 'USD',
            'input_cache_hit_per_million': float(peak['input_cache_hit']),
            'input_cache_miss_per_million': float(peak['input_cache_miss']),
            'output_per_million': float(peak['output']),
            'source_date': snap.get('source_date'),
            'mode': 'configured_peak_price',
        }
    if provider == 'alibaba_cloud_bailian_business_space':
        snap = model_config.get('pricing_snapshot_cny_per_million_tokens') or {}
        _require(all(k in snap for k in ('input', 'output_including_reasoning')), 'bailian_pricing_required')
        return {
            'currency': 'CNY',
            'input_cache_hit_per_million': float(snap.get('cache_hit_input', snap['input'])),
            'input_cache_miss_per_million': float(snap['input']),
            'output_per_million': float(snap['output_including_reasoning']),
            'source_date': snap.get('source_date'),
            'mode': 'configured_list_price_no_promo',
        }
    raise ValueError('unsupported_pricing_provider:' + str(provider))


def subject_max_tokens(model_config):
    section = model_config.get('subject')
    if not isinstance(section, dict):
        raise ValueError('subject_config_required_for_budget_guard')
    value = int(section.get('max_tokens', 0))
    _require(value > 0, 'positive_subject_max_tokens_required')
    return value


def conservative_call_reservation(messages, model_config):
    """Conservative pre-call reservation using UTF-8 byte count as input proxy.

    This is deliberately a budgeting guard rather than a provider billing oracle.
    The actual post-call estimate uses provider-reported token usage.
    """
    policy = pricing_policy(model_config)
    payload_bytes = len(json.dumps(messages, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
    max_output = subject_max_tokens(model_config)
    input_cost = payload_bytes * policy['input_cache_miss_per_million'] / 1_000_000
    output_cost = max_output * policy['output_per_million'] / 1_000_000
    return {
        'input_proxy_units': payload_bytes,
        'max_output_tokens': max_output,
        'reserved_cost': input_cost + output_cost,
        'currency': policy['currency'],
        'pricing_mode': policy['mode'],
    }


def observed_cost_from_usage(usage, model_config):
    usage = usage or {}
    policy = pricing_policy(model_config)
    prompt_total = float(usage.get('prompt_tokens', 0) or 0)
    hit = float(usage.get('prompt_cache_hit_tokens', 0) or 0)
    miss = float(usage.get('prompt_cache_miss_tokens', 0) or 0)
    if hit <= 0 and miss <= 0:
        miss = prompt_total
    elif hit + miss < prompt_total:
        miss += prompt_total - hit - miss
    completion = float(usage.get('completion_tokens', 0) or 0)
    cost = (
        hit * policy['input_cache_hit_per_million']
        + miss * policy['input_cache_miss_per_million']
        + completion * policy['output_per_million']
    ) / 1_000_000
    return {
        'estimated_cost': cost,
        'currency': policy['currency'],
        'pricing_mode': policy['mode'],
        'prompt_tokens': prompt_total,
        'prompt_cache_hit_tokens': hit,
        'prompt_cache_miss_tokens': miss,
        'completion_tokens': completion,
    }


class BudgetedProvider:
    """Wrap a subject provider with pre-call reservation and post-call accounting."""
    def __init__(self, upstream, model_config, spending_ceiling, currency, max_calls):
        self.upstream = upstream
        self.model_config = model_config
        self.spending_ceiling = float(spending_ceiling)
        self.currency = str(currency).upper()
        self.max_calls = int(max_calls)
        _require(self.spending_ceiling > 0, 'positive_spending_ceiling_required')
        _require(self.max_calls > 0, 'positive_max_calls_required')
        policy = pricing_policy(model_config)
        _require(self.currency == policy['currency'], 'currency_does_not_match_model_pricing_snapshot')
        self.calls_started = 0
        self.calls_completed = 0
        self.estimated_spend = 0.0
        self.records = []

    def complete_agent(self, messages, metadata=None):
        if self.calls_started >= self.max_calls:
            raise BudgetExceeded('subject_call_cap_reached')
        reservation = conservative_call_reservation(messages, self.model_config)
        if self.estimated_spend + reservation['reserved_cost'] > self.spending_ceiling:
            raise BudgetExceeded(
                'pre_call_reservation_would_exceed_spending_ceiling:'
                f" observed={self.estimated_spend:.8f} reserve={reservation['reserved_cost']:.8f} "
                f"ceiling={self.spending_ceiling:.8f} {self.currency}"
            )

        self.calls_started += 1
        call_number = self.calls_started
        response = self.upstream.complete_agent(messages, metadata=metadata)
        observed = observed_cost_from_usage(response.get('usage') or {}, self.model_config)
        self.estimated_spend += observed['estimated_cost']
        self.calls_completed += 1
        self.records.append({
            'call_number': call_number,
            'metadata': metadata or {},
            'reservation': reservation,
            'observed': observed,
            'cumulative_estimated_spend': self.estimated_spend,
        })
        if self.estimated_spend > self.spending_ceiling:
            # Preserve the completed call as evidence but stop before another call.
            raise BudgetExceeded(
                'observed_spend_exceeded_ceiling_after_completed_call:'
                f" {self.estimated_spend:.8f}>{self.spending_ceiling:.8f} {self.currency}"
            )
        return response

    def summary(self):
        return {
            'currency': self.currency,
            'spending_ceiling': self.spending_ceiling,
            'max_calls': self.max_calls,
            'calls_started': self.calls_started,
            'calls_completed': self.calls_completed,
            'estimated_spend': self.estimated_spend,
            'pricing_policy': pricing_policy(self.model_config),
            'records': list(self.records),
            'financial_boundary_note': (
                'Pre-call reservation uses a conservative UTF-8-byte input proxy plus configured max output. '
                'Post-call accounting uses provider-reported usage. This is an engineering guard, not a provider invoice guarantee.'
            ),
        }
