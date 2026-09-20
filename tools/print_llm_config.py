from dotenv import load_dotenv, find_dotenv
import os
from urllib.parse import urlparse

load_dotenv(find_dotenv(), override=True)

# Non-sensitive diagnostics: provider, model name, numeric settings, and presence flags only.
provider = os.getenv("LLM_PROVIDER") or os.getenv("NORMA_LLM_PROVIDER") or "anthropic"
model = os.getenv("LLM_MODEL") or os.getenv("NORMA_LLM_MODEL")
temperature = os.getenv("LLM_TEMPERATURE") or os.getenv("NORMA_LLM_TEMPERATURE")
max_tokens = os.getenv("LLM_MAX_TOKENS") or os.getenv("NORMA_LLM_MAX_TOKENS")
base_url = os.getenv("LLM_BASE_URL") or os.getenv("NORMA_LLM_BASE_URL") or os.getenv("LLM_URL")

# Redact base_url to host only to avoid accidental disclosure of tokens embedded in URLs
def _redact_base_url(url: str | None) -> str | None:
    if not url:
        return None
    try:
        p = urlparse(url)
        host = p.netloc or p.path
        return f"{p.scheme}://{host}" if p.scheme else host
    except Exception:
        return "<redacted>"

print("provider=", provider)
print("model=", model)
print("temperature=", temperature)
print("max_tokens=", max_tokens)
print("base_url_host=", _redact_base_url(base_url))

# Do NOT print raw API keys or any secret values — only indicate presence.
print("OPENROUTER_API_KEY present=", bool(os.getenv("OPENROUTER_API_KEY")))
print("ANTHROPIC_API_KEY present=", bool(os.getenv("ANTHROPIC_API_KEY")))
print("OPENAI_API_KEY present=", bool(os.getenv("OPENAI_API_KEY")))

# show which anorm is resolved in current shell (if available)
try:
    import shutil
    anorm_path = shutil.which('anorm')
    print('anorm on PATH:', anorm_path)
except Exception:
    pass
