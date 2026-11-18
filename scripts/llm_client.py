"""One place that talks to an LLM over an API link. Nothing secret is stored in files.
Set these environment variables (or pass them as arguments):
  LLM_BASE_URL   e.g. https://api.openai.com/v1   or   https://api.anthropic.com   or your own server's /v1
  LLM_API_KEY    the key
  LLM_MODEL      the model name
  LLM_STYLE      'openai' (default; works for most servers: OpenAI, vLLM, Ollama, OpenRouter...) or 'anthropic'
Every call is appended to work/llm_log.jsonl (prompt, answer, model, seconds) so runs can be audited."""
import os, json, time, requests

LOG = os.path.join(os.environ.get('RANK_WORK', 'C:/ranking_data/work'), 'llm_log.jsonl')

class LLMConfigError(RuntimeError):
    pass

def chat(messages, system=None, max_tokens=2000, temperature=0.0, base_url=None, api_key=None, model=None, style=None, tag=''):
    base_url = (base_url or os.environ.get('LLM_BASE_URL', '')).rstrip('/')
    api_key = api_key or os.environ.get('LLM_API_KEY', '')
    model = model or os.environ.get('LLM_MODEL', '')
    style = style or os.environ.get('LLM_STYLE', 'openai')
    missing = [n for n, v in (('LLM_BASE_URL', base_url), ('LLM_API_KEY', api_key), ('LLM_MODEL', model)) if not v]
    if missing:
        raise LLMConfigError('Missing: ' + ', '.join(missing) + '. Set them as environment variables.')
    t0 = time.time()
    for attempt in range(6):
        if style == 'anthropic':
            r = requests.post(base_url + '/v1/messages', timeout=180,
                headers={'x-api-key': api_key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json'},
                json={'model': model, 'max_tokens': max_tokens, 'temperature': temperature,
                      **({'system': system} if system else {}), 'messages': messages})
        else:
            msgs = ([{'role': 'system', 'content': system}] if system else []) + messages
            r = requests.post(base_url + '/chat/completions', timeout=180,
                headers={'Authorization': 'Bearer ' + api_key, 'content-type': 'application/json'},
                json={'model': model, 'max_tokens': max_tokens, 'temperature': temperature, 'messages': msgs})
        if r.status_code == 200: break
        if r.status_code in (429, 500, 502, 503, 529): time.sleep(2 ** attempt); continue
        raise RuntimeError(f'LLM API error {r.status_code}: {r.text[:300]}')
    else:
        raise RuntimeError('LLM API kept failing: ' + r.text[:300])
    j = r.json()
    text = (''.join(b.get('text', '') for b in j['content']) if style == 'anthropic' else j['choices'][0]['message']['content'])
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(json.dumps({'t': time.strftime('%Y-%m-%d %H:%M:%S'), 'tag': tag, 'model': model, 'secs': round(time.time() - t0, 2),
                            'system': system, 'messages': messages, 'answer': text}, ensure_ascii=False) + '\n')
    return text

if __name__ == '__main__':      # python llm_client.py  ->  one tiny test call
    try:
        print(chat([{'role': 'user', 'content': 'Reply with the single word: ready'}], max_tokens=10, tag='selftest'))
    except LLMConfigError as e:
        print('Not configured:', e)
