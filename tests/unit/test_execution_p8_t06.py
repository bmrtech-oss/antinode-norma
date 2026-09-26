from antinode_norma.execution.flake import FlakeDetector


def test_flake_detector_flakiness_analysis(tmp_path):
    storage = tmp_path / "flake_history.json"
    detector = FlakeDetector(storage_path=storage)

    # 4 passes, 1 failure for TC-101 (20% failure/flake rate)
    for _ in range(4):
        detector.record_run_result("TC-101", passed=True)
    detector.record_run_result("TC-101", passed=False)

    # 5 passes for TC-102 (0% flake rate)
    for _ in range(5):
        detector.record_run_result("TC-102", passed=True)

    records = detector.analyze_flakiness(threshold=0.20)
    record_map = {r.test_id: r for r in records}

    assert record_map["TC-101"].is_flaky is True
    assert record_map["TC-101"].flake_rate == 0.20
    assert record_map["TC-102"].is_flaky is False
    assert record_map["TC-102"].flake_rate == 0.0


def test_flake_detector_persistence(tmp_path):
    storage = tmp_path / "flake_history.json"
    d1 = FlakeDetector(storage_path=storage)
    d1.record_run_result("TC-201", passed=True)
    d1.record_run_result("TC-201", passed=False)

    d2 = FlakeDetector(storage_path=storage)
    records = d2.analyze_flakiness(threshold=0.10)
    assert len(records) == 1
    assert records[0].test_id == "TC-201"
    assert records[0].is_flaky is True


def test_flake_detector_database_persistence(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'norma.db'}"
    detector = FlakeDetector(database_url=database_url)
    detector.record_run_result("TC-301", passed=True)
    detector.record_run_result("TC-301", passed=False)

    restored = FlakeDetector(database_url=database_url)
    assert restored.history["TC-301"] == {"passed": 1, "failed": 1}
