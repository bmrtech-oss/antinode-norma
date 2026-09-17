from antinode_norma.evaluate.cli_eval import run_eval_ci


def test_run_eval_ci_success():
    status = run_eval_ci()
    assert status == 0
