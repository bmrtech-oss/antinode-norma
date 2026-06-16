import os
import json
from typing import Callable, Dict, Any

def create_llm_callable(config: Dict[str, Any]) -> Callable[[str], str]:
    provider = config.get("provider", "anthropic").lower()
    
    if provider == "anthropic":
        from anthropic import Anthropic
        client = Anthropic(api_key=config.get("api_key") or os.getenv("ANTHROPIC_API_KEY"))
        model = config.get("model", "claude-3-5-sonnet-20241022")
        temperature = config.get("temperature", 0.2)
        max_tokens = config.get("max_tokens", 1024)
        
        def anthropic_call(prompt: str) -> str:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        return anthropic_call
    
    elif provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=config.get("api_key") or os.getenv("OPENAI_API_KEY"))
        model = config.get("model", "gpt-4o")
        temperature = config.get("temperature", 0.2)
        max_tokens = config.get("max_tokens", 1024)
        
        def openai_call(prompt: str) -> str:
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        return openai_call
    
    elif provider == "openrouter":
        from openai import OpenAI
        base_url = config.get("base_url", "https://openrouter.ai/api/v1")
        api_key = config.get("api_key") or os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY is required for openrouter provider")
        client = OpenAI(base_url=base_url, api_key=api_key)
        model = config.get("model", "openai/gpt-oss-120b:free")
        temperature = config.get("temperature", 0.2)
        max_tokens = config.get("max_tokens", 1024)
        extra_body = config.get("extra_body", {})
        if "provider" not in extra_body:
            extra_body["provider"] = {"require_parameters": True}

        def openrouter_call(prompt: str) -> str:
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                extra_body=extra_body
            )
            return response.choices[0].message.content # type: ignore
        return openrouter_call
    
    elif provider == "local":
        import requests
        url = config.get("url")
        if not url:
            raise ValueError("Local LLM requires 'url'")
        max_tokens = config.get("max_tokens", 1024)
        def local_call(prompt: str) -> str:
            resp = requests.post(url, json={"prompt": prompt, "max_tokens": max_tokens})
            return resp.json()["response"]
        return local_call
    
    elif provider == "mock":
        def mock_call(prompt: str) -> str:
            return json.dumps({
                "role": "tester",
                "action": "test action",
                "benefit": "test benefit",
                "acceptance_criteria": ["criterion one", "criterion two"]
            })
        return mock_call
    
    else:
        raise ValueError(f"Unknown provider: {provider}")