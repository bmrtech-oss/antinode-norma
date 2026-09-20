import os
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

base = os.getenv('LLM_BASE_URL') or os.getenv('LLM_URL') or 'https://openrouter.ai/api/v1'
api_key = os.getenv('OPENROUTER_API_KEY')
model = os.getenv('LLM_MODEL')

print('LLM_BASE_URL=', base)
print('LLM_MODEL=', model)
print('OPENROUTER_API_KEY=', (api_key[:8] + '...') if api_key else None)

try:
    from openai import OpenAI
    client = OpenAI(base_url=base, api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        max_tokens=10,
        messages=[{"role": "user", "content": "Say hello"}],
    )
    print('RESPONSE:', json.dumps(resp.__dict__, default=str))
except Exception as e:
    print('EXCEPTION:', type(e).__name__, str(e))
    try:
        import traceback
        traceback.print_exc()
    except Exception:
        pass
