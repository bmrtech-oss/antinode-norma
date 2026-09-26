from pathlib import Path

from antinode_aegis.calibration import CalibrationDataset, calibration_metrics


def test_calibration_fixture_metrics():
    dataset = CalibrationDataset.from_json(Path("tests/fixtures/calibration_p12_t05.json"))
    metrics = calibration_metrics(dataset, bins=10)

    assert dataset.version == "2026-09-25.v1"
    assert metrics["ece"] == 0.15
    assert metrics["mce"] == 0.2
    assert metrics["brier"] == 0.025


def test_empty_calibration_dataset():
    dataset = CalibrationDataset(version="test", examples=[])
    assert calibration_metrics(dataset) == {"ece": 0.0, "mce": 0.0, "brier": 0.0}
