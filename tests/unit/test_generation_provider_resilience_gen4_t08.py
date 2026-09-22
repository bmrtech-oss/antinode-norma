import threading
import time

import pytest

from antinode_norma.server import generation_worker


def _configure(monkeypatch, **values):
    for name, value in values.items():
        monkeypatch.setenv(name, str(value))
    generation_worker._provider_circuits.clear()


def test_provider_retries_with_bounded_backoff_and_recovers(monkeypatch):
    _configure(monkeypatch, NORMA_GENERATION_PROVIDER_MAX_RETRIES=2,
               NORMA_GENERATION_PROVIDER_RETRY_BASE_SECONDS=0,
               NORMA_GENERATION_CIRCUIT_FAILURE_THRESHOLD=3)
    calls = []

    def provider(_prompt):
        calls.append(True)
        if len(calls) < 3:
            raise RuntimeError("secret provider detail")
        return "feature"

    result = generation_worker.execute_provider(
        provider, "prompt", threading.Event(), provider_name="test-recovery")
    assert result == "feature"
    assert len(calls) == 3


def test_provider_timeout_opens_circuit_without_leaking_error(monkeypatch):
    _configure(monkeypatch, NORMA_GENERATION_PROVIDER_TIMEOUT_SECONDS=0.01,
               NORMA_GENERATION_PROVIDER_MAX_RETRIES=0,
               NORMA_GENERATION_CIRCUIT_FAILURE_THRESHOLD=1,
               NORMA_GENERATION_CIRCUIT_RESET_SECONDS=60)

    with pytest.raises(generation_worker.ProviderExecutionError, match="provider timeout"):
        generation_worker.execute_provider(
            lambda _prompt: time.sleep(1), "prompt", threading.Event(),
            provider_name="test-timeout")
    with pytest.raises(generation_worker.ProviderCircuitOpenError):
        generation_worker.execute_provider(
            lambda _prompt: "should not run", "prompt", threading.Event(),
            provider_name="test-timeout")


def test_provider_backoff_is_cancellable(monkeypatch):
    _configure(monkeypatch, NORMA_GENERATION_PROVIDER_MAX_RETRIES=2,
               NORMA_GENERATION_PROVIDER_RETRY_BASE_SECONDS=10)
    cancelled = threading.Event()

    def provider(_prompt):
        cancelled.set()
        raise RuntimeError("provider detail")

    with pytest.raises(InterruptedError):
        generation_worker.execute_provider(
            provider, "prompt", cancelled, provider_name="test-cancel")


def test_provider_failure_redacts_exception_message(monkeypatch):
    _configure(monkeypatch, NORMA_GENERATION_PROVIDER_MAX_RETRIES=0,
               NORMA_GENERATION_CIRCUIT_FAILURE_THRESHOLD=3)
    secret = "provider-secret-value"

    def provider(_prompt):
        raise RuntimeError(secret)

    with pytest.raises(generation_worker.ProviderExecutionError) as raised:
        generation_worker.execute_provider(
            provider, "prompt containing secret", threading.Event(),
            provider_name="test-redaction")

    assert str(raised.value) == "provider failure after retries"
    assert secret not in str(raised.value)
