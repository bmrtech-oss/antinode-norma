import os
import yaml
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv, find_dotenv

from .core.quality import compute_quality
from .core.parser import parse_story
from .core.gherkin_generator import generate_gherkin
from .core.validator import validate_gherkin
from .utils.llm_factory import create_llm_callable
from .utils.file_writer import write_feature_file

# Load .env from the repository if present. Do NOT override existing
# environment variables so subprocesses and CI can set overrides.
load_dotenv(find_dotenv(), override=False)

# Load norma.config.yml if present (used as defaults; env vars take precedence)
_NORMA_CONFIG: Dict[str, Any] = {}
try:
    _cfg_path = os.path.join(os.path.dirname(__file__), "..", "norma.config.yml")
    _cfg_path = os.path.abspath(_cfg_path)
    if os.path.exists(_cfg_path):
        with open(_cfg_path, "r", encoding="utf-8") as fh:
            _NORMA_CONFIG = yaml.safe_load(fh) or {}
except Exception:
    _NORMA_CONFIG = {}


def get_llm_callable():
    # helpers: env overrides, then norma.config.yml, then built-in defaults
    norma_llm = _NORMA_CONFIG.get("llm", {}) if isinstance(_NORMA_CONFIG, dict) else {}

    def _env_or_cfg(env_keys, cfg_key, default=None):
        # env_keys: list of env var names to check in order
        for k in (env_keys or []):
            v = os.getenv(k)
            if v is not None and v != "":
                return v
        # fallback to cfg
        if cfg_key and (cfg_key in norma_llm):
            return norma_llm[cfg_key]
        return default

    provider = _env_or_cfg(["LLM_PROVIDER", "NORMA_LLM_PROVIDER"], "provider", "anthropic")

    # API key resolution: check provider-specific envs first, then config's api_key_env, then common env names
    api_key = None
    prov = (provider or "").lower()
    if prov == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("NORMA_LLM_API_KEY")
    elif prov == "openai":
        api_key = os.getenv("OPENAI_API_KEY") or os.getenv("NORMA_LLM_API_KEY")
    elif prov == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("NORMA_LLM_API_KEY")
    elif prov in ("gemini", "google", "google-gemini"):
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("NORMA_LLM_API_KEY")
    else:
        api_key = os.getenv("NORMA_LLM_API_KEY") or os.getenv("LLM_API_KEY")

    # If norma.config.yml provided an api_key_env name, prefer that when no env found
    if not api_key and isinstance(norma_llm.get("api_key_env"), str):
        api_key = os.getenv(norma_llm.get("api_key_env"))

    model = _env_or_cfg(["LLM_MODEL", "NORMA_LLM_MODEL"], "model", None)
    temperature = float(_env_or_cfg(["LLM_TEMPERATURE", "NORMA_LLM_TEMPERATURE"], "temperature", 0.2))
    max_tokens = int(_env_or_cfg(["LLM_MAX_TOKENS", "NORMA_LLM_MAX_TOKENS"], "max_tokens", 1024))
    base_url = _env_or_cfg(["LLM_BASE_URL", "NORMA_LLM_BASE_URL", "LLM_URL"], "base_url", None)

    if not model:
        raise ValueError("LLM_MODEL is required. Set LLM_MODEL or NORMA_LLM_MODEL in the environment or config.")

    config = {
        "provider": provider,
        "api_key": api_key,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "base_url": base_url,
        "url": base_url,
    }
    # lightweight trace for provider selection (helpful in subprocess diagnostics)
    try:
        trace_dir = os.path.join(os.getcwd(), ".tmp")
        os.makedirs(trace_dir, exist_ok=True)
        trace_file = os.path.join(trace_dir, "anorm_runner_trace.log")
        with open(trace_file, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.utcnow().isoformat()}Z get_llm_callable:provider={provider}\n")
    except Exception:
        pass
    llm = create_llm_callable(config)
    try:
        if getattr(llm, "_is_mock", False):
            with open(trace_file, "a", encoding="utf-8") as fh:
                fh.write(f"{datetime.utcnow().isoformat()}Z get_llm_callable:mock_callable=True\n")
    except Exception:
        pass
    return llm


def get_step_definitions(keyword: str = None):
    steps = [
        "Given the user is on the login page",
        "When the user clicks 'Forgot password'",
        "Then a password reset email is sent",
        "Given a valid reset token exists",
        "When the user submits a new password",
        "Then the password is updated",
    ]
    if keyword:
        steps = [s for s in steps if s.lower().startswith(keyword.lower())]
    return steps


async def run_agent_from_raw(
    raw_story: str, quality_only: bool = False
) -> Dict[str, Any]:
    """Run the Norma agent from raw story text."""
    # lightweight tracing to help debug hangs in subprocess test runs
    def _trace(msg: str):
        try:
            trace_dir = os.path.join(os.getcwd(), ".tmp")
            os.makedirs(trace_dir, exist_ok=True)
            trace_file = os.path.join(trace_dir, "anorm_runner_trace.log")
            with open(trace_file, "a", encoding="utf-8") as fh:
                fh.write(f"{datetime.utcnow().isoformat()}Z {msg}\n")
        except Exception:
            pass

    _trace("run_agent_from_raw:start")
    llm_call = get_llm_callable()
    _trace("run_agent_from_raw:get_llm_callable:done")
    _trace("run_agent_from_raw:before_parse_story")
    try:
        story = parse_story(raw_story, llm_call)
        _trace("run_agent_from_raw:parse_story:done")
    except Exception as e:
        _trace(f"run_agent_from_raw:parse_story:exception={e}")
        raise
    _trace("run_agent_from_raw:before_compute_quality")
    report = compute_quality(story)
    _trace(f"run_agent_from_raw:compute_quality:passes_invest={report.passes_invest}")
    if quality_only:
        return {
            "quality_score": report.quality_score,
            "passes_invest": report.passes_invest,
            "issues": report.issues,
            "suggestions": report.suggestions,
        }
    if not report.passes_invest:
        return {
            "error": "Quality check failed – story does not meet INVEST criteria",
            "issues": report.issues,
            "suggestions": report.suggestions,
        }
    step_defs = get_step_definitions()
    _trace("run_agent_from_raw:get_step_definitions:done")
    _trace("run_agent_from_raw:before_generate_gherkin")
    gherkin = generate_gherkin(story, step_defs, llm_call)
    _trace("run_agent_from_raw:generate_gherkin:done")
    validation = validate_gherkin(gherkin)
    _trace(f"run_agent_from_raw:validate_gherkin:valid={validation.valid}")
    if not validation.valid:
        return {"error": "Gherkin validation failed", "errors": validation.errors}
    output_dir = os.getenv("NORMA_OUTPUT_DIR", "features")
    safe_action = story.action.lower().replace(" ", "_")
    file_path = os.path.join(output_dir, f"{safe_action}.feature")
    write_feature_file(file_path, gherkin)
    return {"feature_path": file_path, "validation_passed": True}


async def run_bdd_agent(raw_story: str, max_iterations: int = 3) -> Dict[str, Any]:
    """Run the autonomous BDD agent on a story."""
    return await run_agent_from_raw(raw_story)
