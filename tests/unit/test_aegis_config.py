import pytest

from antinode_aegis.config import AegisConfig


def test_aegis_config_rejects_unbounded_repair_attempts() -> None:
    with pytest.raises(ValueError):
        AegisConfig(max_repair_attempts=11)
