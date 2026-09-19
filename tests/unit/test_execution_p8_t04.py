import xml.etree.ElementTree as ET
from antinode_norma.execution.parallel import ParallelExecutionResult, TaskResult
from antinode_norma.execution.reporters import ExecutionReporter


def test_generate_junit_xml(tmp_path):
    res = ParallelExecutionResult(
        total_tasks=2,
        passed_count=1,
        failed_count=1,
        duration_seconds=1.5,
        results=[
            TaskResult(task_id="TC-101", passed=True, duration_seconds=0.5),
            TaskResult(task_id="TC-102", passed=False, error="Step failed", duration_seconds=1.0),
        ],
    )
    xml_file = tmp_path / "junit.xml"
    ExecutionReporter.generate_junit_xml(res, xml_file)

    assert xml_file.exists()
    tree = ET.parse(xml_file)
    root = tree.getroot()
    assert root.tag == "testsuites"
    suite = root.find("testsuite")
    assert suite.attrib["tests"] == "2"
    assert suite.attrib["failures"] == "1"


def test_generate_allure_results(tmp_path):
    res = ParallelExecutionResult(
        total_tasks=1,
        passed_count=1,
        failed_count=0,
        duration_seconds=0.8,
        results=[
            TaskResult(task_id="TC-201", passed=True, duration_seconds=0.8),
        ],
    )
    allure_dir = tmp_path / "allure-results"
    ExecutionReporter.generate_allure_results(res, allure_dir)

    json_files = list(allure_dir.glob("*-result.json"))
    assert len(json_files) == 1


def test_generate_html_report(tmp_path):
    res = ParallelExecutionResult(
        total_tasks=1,
        passed_count=1,
        failed_count=0,
        duration_seconds=0.5,
        results=[
            TaskResult(task_id="TC-301", passed=True, duration_seconds=0.5),
        ],
    )
    html_file = tmp_path / "report.html"
    ExecutionReporter.generate_html_report(res, html_file)

    assert html_file.exists()
    content = html_file.read_text(encoding="utf-8")
    assert "Norma BDD Execution Summary" in content
    assert "TC-301" in content
