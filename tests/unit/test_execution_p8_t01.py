import time
from antinode_norma.execution.parallel import ParallelExecutor


def test_parallel_executor_success():
    executor = ParallelExecutor(max_workers=2)
    tasks = [{"id": "t1", "val": 1}, {"id": "t2", "val": 2}]

    def task_fn(item):
        time.sleep(0.01)
        return item["val"] * 10

    res = executor.execute_parallel(tasks, task_fn)
    assert res.total_tasks == 2
    assert res.passed_count == 2
    assert res.failed_count == 0
    assert res.duration_seconds > 0.0


def test_parallel_executor_with_failures():
    executor = ParallelExecutor(max_workers=2)
    tasks = [{"id": "t1", "fail": False}, {"id": "t2", "fail": True}]

    def task_fn(item):
        if item["fail"]:
            raise ValueError("Task failed intentionally")
        return "ok"

    res = executor.execute_parallel(tasks, task_fn)
    assert res.total_tasks == 2
    assert res.passed_count == 1
    assert res.failed_count == 1
    failed_results = [r for r in res.results if not r.passed]
    assert len(failed_results) == 1
    assert "Task failed intentionally" in failed_results[0].error


def test_parallel_executor_empty():
    executor = ParallelExecutor()
    res = executor.execute_parallel([], lambda x: x)
    assert res.total_tasks == 0
    assert res.passed_count == 0
