import json
import urllib.error
import urllib.request

from django.conf import settings


def _anthropic_client():
    try:
        import anthropic
    except ImportError:
        return None
    api_key = getattr(settings, 'AI_ASSIST_API_KEY', '') or getattr(settings, 'ANTHROPIC_API_KEY', '')
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)


def call_llm(messages, temperature=0.7, max_tokens=2048):
    """Send *messages* to the configured LLM and return the text reply.

    Resolution order:
    1. ``AI_ASSIST_API_URL`` (OpenAI-compatible endpoint) + ``AI_ASSIST_API_KEY``
    2. The ``anthropic`` SDK (if installed and ``ANTHROPIC_API_KEY`` set)

    Returns ``None`` when no provider is configured so callers can fall back
    to a deterministic stub.
    """
    api_url = getattr(settings, 'AI_ASSIST_API_URL', '') or getattr(settings, 'AI_API_URL', '')
    api_key = getattr(settings, 'AI_ASSIST_API_KEY', '') or getattr(settings, 'ANTHROPIC_API_KEY', '')

    if api_url and api_key:
        return _call_openai_compatible(messages, api_url, api_key, temperature, max_tokens)

    client = _anthropic_client()
    if client is not None:
        model = getattr(settings, 'AI_ASSIST_MODEL', 'claude-3-5-sonnet-20240620')
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=messages,
            )
            return resp.content[0].text
        except Exception:
            return None
    return None


def _call_openai_compatible(messages, url, key, temperature, max_tokens):
    model = getattr(settings, 'AI_ASSIST_MODEL', 'gpt-4o-mini')
    payload = json.dumps({
        'model': model,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': max_tokens,
    }).encode('utf-8')
    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
            method='POST',
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        if 'choices' in data:
            return data['choices'][0]['message']['content']
        if 'content' in data:
            return data['content'][0]['text']
        return None
    except (urllib.error.URLError, urllib.error.HTTPError, Exception):
        return None
