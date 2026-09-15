import time
from typing import Callable, Any, Tuple, Type, Optional, List
from pydantic import BaseModel, Field


class RetryResult(BaseModel):
    attempts: int = 1
    passed: bool = True
    final_result: Optional[Any] = None
    last_error: Optional[str] = None
    delays_taken: List[float] = Field(default_factory=list)


def retry_with_backoff(
    func: Callable[[], Any],
    max_retries: int = 3,
    initial_delay: float = 0.1,
    backoff_factor: float = 2.0,
    max_delay: float = 10.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    sleep_fn: Callable[[float], None] = time.sleep,
) -> RetryResult:
    """
    Execute callable `func` retrying on specified exceptions with exponential backoff.
    """
    current_delay = initial_delay
    delays_taken: List[float] = []

    for attempt in range(1, max_retries + 1):
        try:
            result = func()
            return RetryResult(
                attempts=attempt,
                passed=True,
                final_result=result,
                delays_taken=delays_taken,
            )
        except exceptions as e:
            last_err = str(e)
            if attempt == max_retries:
                return RetryResult(
                    attempts=attempt,
                    passed=False,
                    last_error=last_err,
                    delays_taken=delays_taken,
                )

            delays_taken.append(round(current_delay, 4))
            sleep_fn(current_delay)
            current_delay = min(current_delay * backoff_factor, max_delay)

    return RetryResult(
        attempts=max_retries,
        passed=False,
        last_error="Max retries reached",
        delays_taken=delays_taken,
    )
