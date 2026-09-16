import json


class ScriptedProvider:
    """Engineering-only provider used by offline preflight. Never scientific evidence."""
    def __init__(self, scripted):
        self.scripted = list(scripted)
        self.index = 0

    def complete_agent(self, messages, metadata=None):
        if self.index >= len(self.scripted):
            obj = {'decision_summary':'preflight stop','actions':[{'type':'finalize','answer':'preflight final'}]}
        else:
            obj = self.scripted[self.index]
        self.index += 1
        return {
            'content': json.dumps(obj, ensure_ascii=False),
            'response_id': f'stub-{self.index}',
            'model': 'SCRIPTED_PREFLIGHT_ONLY',
            'usage': {},
        }


class DeepSeekArenaProvider:
    def __init__(self, config):
        from adapters.deepseek_chat import chat_completion, extract_content
        self.config = config
        self._chat_completion = chat_completion
        self._extract_content = extract_content

    def complete_agent(self, messages, metadata=None):
        response = self._chat_completion(
            self.config, messages, evaluator=False, response_format_json=True
        )
        return {
            'content': self._extract_content(response),
            'response_id': response.get('id'),
            'model': response.get('model'),
            'usage': response.get('usage') or {},
            'transport_latency_ms': response.get('_transport_latency_ms'),
            'provider_response': response,
            'finish_reason': (response.get('choices') or [{}])[0].get('finish_reason'),
        }


class BailianArenaProvider:
    """Bailian subject provider. Requires an explicit `subject` block in config.

    Existing reviewer-only Bailian configs are intentionally rejected rather than
    silently reusing evaluator parameters for subject collection.
    """
    def __init__(self, config):
        from adapters.bailian_openai_chat import chat_completion, extract_content
        if not isinstance(config.get('subject'), dict):
            raise ValueError('bailian_subject_config_required')
        self.config = config
        self._chat_completion = chat_completion
        self._extract_content = extract_content

    def complete_agent(self, messages, metadata=None):
        section = self.config['subject']
        response = self._chat_completion(
            messages,
            response_format_json=True,
            max_tokens=int(section['max_tokens']),
            temperature=float(section['temperature']),
            enable_thinking=section.get('enable_thinking'),
            thinking_budget=section.get('thinking_budget'),
        )
        return {
            'content': self._extract_content(response),
            'response_id': response.get('id'),
            'model': response.get('model'),
            'usage': response.get('usage') or {},
            'transport_latency_ms': response.get('_transport_latency_ms'),
            'provider_response': response,
            'finish_reason': (response.get('choices') or [{}])[0].get('finish_reason'),
        }


def provider_from_config(config):
    provider = config.get('provider')
    if provider == 'deepseek':
        return DeepSeekArenaProvider(config)
    if provider == 'alibaba_cloud_bailian_business_space':
        return BailianArenaProvider(config)
    raise ValueError('unsupported_arena_provider:' + str(provider))
