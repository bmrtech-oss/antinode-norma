import os
import json
from typing import Callable, Dict, Any


def create_llm_callable(config: Dict[str, Any]) -> Callable[[str], str]:
    provider = config.get("provider", "anthropic").lower()

    if provider == "anthropic":
        from anthropic import Anthropic

        client = Anthropic(
            api_key=config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        )
        model = config.get("model", "claude-3-5-sonnet-20241022")
        temperature = config.get("temperature", 0.2)
        max_tokens = config.get("max_tokens", 1024)

        def anthropic_call(prompt: str) -> str:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
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
                messages=[{"role": "user", "content": prompt}],
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
                extra_body=extra_body,
            )
            return response.choices[0].message.content  # type: ignore

        return openrouter_call

    elif provider in ("gemini", "google", "google-gemini"):
        api_key = config.get("api_key") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY is required for gemini provider")
        model = config.get("model", "gemini-1.5-flash")
        temperature = config.get("temperature", 0.2)
        max_tokens = config.get("max_tokens", 1024)

        try:
            import google.generativeai as genai

            genai.configure(api_key=api_key)
            gen_model = genai.GenerativeModel(
                model_name=model,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )

            def gemini_call(prompt: str) -> str:
                response = gen_model.generate_content(prompt)
                return response.text

            return gemini_call
        except ImportError:
            try:
                from openai import OpenAI

                base_url = config.get("base_url", "https://generativelanguage.googleapis.com/v1beta/openai/")
                client = OpenAI(base_url=base_url, api_key=api_key)

                def gemini_openai_call(prompt: str) -> str:
                    response = client.chat.completions.create(
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return response.choices[0].message.content or ""

                return gemini_openai_call
            except ImportError:
                raise ImportError("Neither 'google-generativeai' nor 'openai' package is installed for gemini provider")

    elif provider == "groq":
        api_key = config.get("api_key") or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is required for groq provider")
        model = config.get("model", "llama-3.3-70b-versatile")
        temperature = config.get("temperature", 0.2)
        max_tokens = config.get("max_tokens", 1024)

        try:
            from groq import Groq

            client = Groq(api_key=api_key)

            def groq_call(prompt: str) -> str:
                response = client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content or ""

            return groq_call
        except ImportError:
            try:
                from openai import OpenAI

                base_url = config.get("base_url", "https://api.groq.com/openai/v1")
                client = OpenAI(base_url=base_url, api_key=api_key)

                def groq_openai_call(prompt: str) -> str:
                    response = client.chat.completions.create(
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return response.choices[0].message.content or ""

                return groq_openai_call
            except ImportError:
                raise ImportError("Neither 'groq' nor 'openai' package is installed for groq provider")

    elif provider in ("mistral", "mistralai"):
        api_key = config.get("api_key") or os.getenv("MISTRAL_API_KEY")
        if not api_key:
            raise ValueError("MISTRAL_API_KEY is required for mistral provider")
        model = config.get("model", "mistral-small-latest")
        temperature = config.get("temperature", 0.2)
        max_tokens = config.get("max_tokens", 1024)

        try:
            from mistralai import Mistral

            client = Mistral(api_key=api_key)

            def mistral_call(prompt: str) -> str:
                response = client.chat.complete(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[{"role": "user", "content": prompt}],
                )
                return response.choices[0].message.content or ""

            return mistral_call
        except (ImportError, AttributeError):
            try:
                from openai import OpenAI

                base_url = config.get("base_url", "https://api.mistral.ai/v1")
                client = OpenAI(base_url=base_url, api_key=api_key)

                def mistral_openai_call(prompt: str) -> str:
                    response = client.chat.completions.create(
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return response.choices[0].message.content or ""

                return mistral_openai_call
            except ImportError:
                raise ImportError("Neither 'mistralai' nor 'openai' package is installed for mistral provider")

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

        def _extract_block(prompt: str, marker: str) -> str:
            if marker in prompt:
                return prompt.split(marker, 1)[1].strip()
            return ""

        def _get_line(prompt: str, marker: str, default: str) -> str:
            val = _extract_block(prompt, marker)
            lines = val.splitlines()
            if lines and lines[0].strip():
                return lines[0].strip()
            return default

        def _parse_story_text(raw_text: str):
            role = "user"
            action = "do something"
            benefit = "achieve value"
            text = raw_text.strip().strip("`\n ")
            text_lower = text.lower()
            if text_lower.startswith("as a "):
                text = text[5:]
                text_lower = text.lower()
                if " so that " in text_lower:
                    idx = text_lower.find(" so that ")
                    before = text[:idx]
                    after = text[idx + 9 :]
                    benefit = after.strip().rstrip(".")
                else:
                    before = text
                before_lower = before.lower()
                if " i want to " in before_lower:
                    idx = before_lower.find(" i want to ")
                    role = before[:idx].strip().rstrip(".")
                    action = before[idx + 11 :].strip().rstrip(".")
            elif text:
                action = text.split(".")[0].strip()
            return role, action, benefit

        def _build_feature(role: str, action: str, benefit: str, criteria: list[str]):
            feature_title = f"{action.capitalize()}"
            scenario_title = f"Generate a feature for {action}"
            steps = [
                f"Given the {role} is on the system page",
                f"When they {action}",
                f"Then the outcome should support {benefit}",
            ]
            return (
                f"Feature: {feature_title}\n\n"
                f"  Scenario: {scenario_title}\n"
                f"    {steps[0]}\n"
                f"    {steps[1]}\n"
                f"    {steps[2]}\n"
            )

        def mock_call(prompt: str) -> str:
            if "Convert the following user story into a JSON object" in prompt:
                raw_story = _extract_block(prompt, "Story:")
                role, action, benefit = _parse_story_text(raw_story)
                return json.dumps(
                    {
                        "role": role,
                        "action": action,
                        "benefit": benefit,
                        "acceptance_criteria": [
                            "The story is converted into a valid JSON schema.",
                            "The story is suitable for Gherkin generation.",
                        ],
                    }
                )
            if "Output ONLY a valid Gherkin feature file" in prompt:
                role = _get_line(prompt, "Role:", "user")
                action = _get_line(prompt, "Action:", "do something")
                benefit = _get_line(prompt, "Benefit:", "get value")
                criteria_block = _extract_block(prompt, "Acceptance criteria:")
                criteria = [
                    line.strip()[2:].strip()
                    for line in criteria_block.splitlines()
                    if line.strip().startswith("- ")
                ]
                return _build_feature(role, action, benefit, criteria)
            return json.dumps(
                {
                    "role": "tester",
                    "action": "perform a test action",
                    "benefit": "validate a test flow",
                    "acceptance_criteria": ["criterion one", "criterion two"],
                }
            )

        return mock_call

    else:
        raise ValueError(f"Unknown provider: {provider}")
