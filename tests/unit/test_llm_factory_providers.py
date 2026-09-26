"""Unit tests for Gemini, Groq, and Mistral LLM factory providers."""

import pytest
from unittest.mock import MagicMock, patch
from antinode_norma.utils.llm_factory import create_llm_callable


def test_gemini_missing_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY or GOOGLE_API_KEY is required"):
        create_llm_callable({"provider": "gemini"})


def test_groq_missing_api_key(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GROQ_API_KEY is required"):
        create_llm_callable({"provider": "groq"})


def test_mistral_missing_api_key(monkeypatch):
    monkeypatch.delenv("MISTRAL_API_KEY", raising=False)
    with pytest.raises(ValueError, match="MISTRAL_API_KEY is required"):
        create_llm_callable({"provider": "mistral"})


def test_gemini_openai_fallback(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("NORMA_LLM_MODEL", raising=False)
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Gemini OpenAI response"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Mock google.generativeai import failure
        with patch.dict("sys.modules", {"google.generativeai": None}):
            llm = create_llm_callable({"provider": "gemini", "api_key": "dummy_key"})
            result = llm("Hello Gemini")
            assert result == "Gemini OpenAI response"


def test_groq_openai_fallback(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("NORMA_LLM_MODEL", raising=False)
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Groq response"))]
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict("sys.modules", {"groq": None}):
            llm = create_llm_callable({"provider": "groq", "api_key": "dummy_key"})
            result = llm("Hello Groq")
            assert result == "Groq response"


def test_mistral_openai_fallback(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("NORMA_LLM_MODEL", raising=False)
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Mistral response"))]
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict("sys.modules", {"mistralai": None}):
            llm = create_llm_callable({"provider": "mistral", "api_key": "dummy_key"})
            result = llm("Hello Mistral")
            assert result == "Mistral response"


def test_anthropic_retries_without_temperature_when_sdk_rejects_it():
    mock_anthropic = MagicMock()
    with patch.dict("sys.modules", {"anthropic": MagicMock(Anthropic=mock_anthropic)}):
        client = MagicMock()
        mock_anthropic.return_value = client
        response = MagicMock()
        response.content = [MagicMock(text="Anthropic response")]
        client.messages.create.side_effect = [
            TypeError("unexpected keyword argument 'temperature'"),
            response,
        ]

        llm = create_llm_callable(
            {
                "provider": "anthropic",
                "api_key": "dummy_key",
                "model": "test-model",
                "temperature": 0.2,
            }
        )
        assert llm("Hello Anthropic") == "Anthropic response"

        first_call = client.messages.create.call_args_list[0].kwargs
        second_call = client.messages.create.call_args_list[1].kwargs
        assert first_call["temperature"] == 0.2
        assert "temperature" not in second_call


def test_anthropic_preserves_temperature_when_sdk_accepts_it():
    mock_anthropic = MagicMock()
    with patch.dict("sys.modules", {"anthropic": MagicMock(Anthropic=mock_anthropic)}):
        client = MagicMock()
        mock_anthropic.return_value = client
        response = MagicMock()
        response.content = [MagicMock(text="Anthropic response")]
        client.messages.create.return_value = response

        llm = create_llm_callable(
            {
                "provider": "anthropic",
                "api_key": "dummy_key",
                "model": "test-model",
                "temperature": 0.7,
            }
        )
        assert llm("Hello Anthropic") == "Anthropic response"
        assert client.messages.create.call_args.kwargs["temperature"] == 0.7


def test_provider_requires_explicit_model_when_missing(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with pytest.raises(ValueError, match="LLM_MODEL is required"):
        create_llm_callable({"provider": "anthropic", "api_key": "dummy_key"})

    with pytest.raises(ValueError, match="LLM_MODEL is required"):
        create_llm_callable({"provider": "openrouter", "api_key": "dummy_key"})

    with pytest.raises(ValueError, match="LLM_MODEL is required"):
        create_llm_callable({"provider": "openai", "api_key": "dummy_key"})
