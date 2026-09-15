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

