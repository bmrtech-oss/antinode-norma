import json
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Union
from antinode_norma.execution.parallel import ParallelExecutionResult


class ExecutionReporter:
    @staticmethod
    def generate_junit_xml(
        result: ParallelExecutionResult, output_path: Union[str, Path]
    ) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        testsuites = ET.Element("testsuites")
        suite = ET.SubElement(
            testsuites,
            "testsuite",
            name="NormaBDDSuite",
            tests=str(result.total_tasks),
            failures=str(result.failed_count),
            time=f"{result.duration_seconds:.4f}",
        )

        for task_res in result.results:
            case = ET.SubElement(
                suite,
                "testcase",
                name=task_res.task_id,
                classname="NormaBDDScenario",
                time=f"{task_res.duration_seconds:.4f}",
            )
            if not task_res.passed:
                failure = ET.SubElement(
                    case, "failure", message=task_res.error or "Scenario execution failed"
                )
                failure.text = task_res.error or "Scenario execution failed"

        tree = ET.ElementTree(testsuites)
        tree.write(path, encoding="utf-8", xml_declaration=True)
        return path

    @staticmethod
    def generate_allure_results(
        result: ParallelExecutionResult, output_dir: Union[str, Path]
    ) -> Path:
        dir_path = Path(output_dir)
        dir_path.mkdir(parents=True, exist_ok=True)

        now_ms = int(time.time() * 1000)

        for task_res in result.results:
            duration_ms = int(task_res.duration_seconds * 1000)
            status = "passed" if task_res.passed else "failed"

            allure_data = {
                "uuid": str(uuid.uuid4()),
                "historyId": task_res.task_id,
                "name": task_res.task_id,
                "status": status,
                "start": now_ms - duration_ms,
                "stop": now_ms,
                "labels": [
                    {"name": "framework", "value": "norma-bdd"},
                    {"name": "suite", "value": "NormaBDDSuite"},
                ],
            }

            if not task_res.passed and task_res.error:
                allure_data["statusDetails"] = {"message": task_res.error}

            result_file = dir_path / f"{uuid.uuid4()}-result.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(allure_data, f, indent=2)

        return dir_path

    @staticmethod
    def generate_html_report(
        result: ParallelExecutionResult, output_path: Union[str, Path]
    ) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        status_class = "pass" if result.failed_count == 0 else "fail"
        rows = []
        for task_res in result.results:
            badge = "<span style='color: green;'>PASS</span>" if task_res.passed else "<span style='color: red;'>FAIL</span>"
            err = f"<br><small>{task_res.error}</small>" if task_res.error else ""
            rows.append(
                f"<tr><td>{task_res.task_id}</td><td>{badge}{err}</td><td>{task_res.duration_seconds:.4f}s</td></tr>"
            )

        table_body = "\n".join(rows)

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Norma BDD Execution Report</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 20px; }}
        h1 {{ color: #333; }}
        .summary {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
        th {{ background: #fafafa; }}
    </style>
</head>
<body>
    <h1>Norma BDD Execution Summary</h1>
    <div class="summary">
        <p><strong>Total Scenarios:</strong> {result.total_tasks}</p>
        <p><strong>Passed:</strong> {result.passed_count} | <strong>Failed:</strong> {result.failed_count}</p>
        <p><strong>Total Duration:</strong> {result.duration_seconds:.4f}s</p>
    </div>
    <table>
        <thead>
            <tr><th>Scenario ID</th><th>Status</th><th>Duration</th></tr>
        </thead>
        <tbody>
            {table_body}
        </tbody>
    </table>
</body>
</html>"""

        with open(path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return path
