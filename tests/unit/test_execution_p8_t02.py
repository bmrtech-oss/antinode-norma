from antinode_norma.execution.retry import retry_with_backoff


def test_retry_success_first_attempt():
    res = retry_with_backoff(lambda: 42, max_retries=3)
    assert res.passed is True
    assert res.attempts == 1
    assert res.final_result == 42
    assert res.delays_taken == []


def test_retry_success_after_transient_failures():
    attempts = 0
    slept = []

    def mock_func():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError(f"Transient error attempt {attempts}")
        return "success"

    res = retry_with_backoff(
        mock_func,
        max_retries=3,
        initial_delay=0.1,
        backoff_factor=2.0,
        exceptions=(ConnectionError,),
        sleep_fn=slept.append,
    )

    assert res.passed is True
    assert res.attempts == 3
    assert res.final_result == "success"
    assert slept == [0.1, 0.2]


def test_retry_exhausted_failures():
    slept = []

    def mock_fail():
        raise RuntimeError("Persistent failure")

    res = retry_with_backoff(
        mock_fail,
        max_retries=3,
        initial_delay=0.1,
        backoff_factor=2.0,
        exceptions=(RuntimeError,),
        sleep_fn=slept.append,
    )

    assert res.passed is False
    assert res.attempts == 3
    assert "Persistent failure" in res.last_error
    assert slept == [0.1, 0.2]
