import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable, List, Any, Dict, Optional
from pydantic import BaseModel, Field


class TaskResult(BaseModel):
    task_id: str
    passed: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0


class ParallelExecutionResult(BaseModel):
    total_tasks: int = 0
    passed_count: int = 0
    failed_count: int = 0
    duration_seconds: float = 0.0
    results: List[TaskResult] = Field(default_factory=list)


class ParallelExecutor:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers

    def execute_parallel(
        self,
        tasks: List[Dict[str, Any]],
        task_fn: Callable[[Dict[str, Any]], Any],
    ) -> ParallelExecutionResult:
        if not tasks:
            return ParallelExecutionResult()

        start_time = time.time()
        results: List[TaskResult] = []

        def worker(task: Dict[str, Any]) -> TaskResult:
            task_id = str(task.get("id", task.get("task_id", "unknown")))
            t0 = time.time()
            try:
                out = task_fn(task)
                dur = time.time() - t0
                return TaskResult(
                    task_id=task_id,
                    passed=True,
                    result=out,
                    duration_seconds=round(dur, 4),
                )
            except Exception as e:
                dur = time.time() - t0
                return TaskResult(
                    task_id=task_id,
                    passed=False,
                    error=str(e),
                    duration_seconds=round(dur, 4),
                )

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {executor.submit(worker, t): t for t in tasks}
            for future in as_completed(future_to_task):
                results.append(future.result())

        total_duration = time.time() - start_time
        passed_cnt = sum(1 for r in results if r.passed)
        failed_cnt = sum(1 for r in results if not r.passed)

        return ParallelExecutionResult(
            total_tasks=len(tasks),
            passed_count=passed_cnt,
            failed_count=failed_cnt,
            duration_seconds=round(total_duration, 4),
            results=results,
        )
