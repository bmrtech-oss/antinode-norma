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


def test_gemini_openai_fallback():
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


def test_groq_openai_fallback():
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


def test_mistral_openai_fallback():
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
