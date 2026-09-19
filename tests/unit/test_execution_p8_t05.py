import pytest
from antinode_norma.execution.cloud import CloudRunner, CloudConfig, CloudProvider


def test_cloud_runner_browserstack_url_and_caps():
    config = CloudConfig(
        provider=CloudProvider.BROWSERSTACK,
        username="bs_user",
        access_key="bs_key",
        browser_name="chrome",
        os_name="Windows",
        os_version="11",
    )
    runner = CloudRunner(config)
    url = runner.build_remote_url()
    caps = runner.build_capabilities()

    assert "bs_user:bs_key@hub-cloud.browserstack.com" in url
    assert caps["browserName"] == "chrome"
    assert caps["bstack:options"]["os"] == "Windows"


def test_cloud_runner_saucelabs():
    config = CloudConfig(
        provider=CloudProvider.SAUCELABS,
        username="sauce_user",
        access_key="sauce_key",
        browser_name="firefox",
    )
    runner = CloudRunner(config)
    url = runner.build_remote_url()
    caps = runner.build_capabilities()

    assert "sauce_user:sauce_key@ondemand.us-west-1.saucelabs.com" in url
    assert "sauce:options" in caps


def test_cloud_runner_lambdatest():
    config = CloudConfig(
        provider=CloudProvider.LAMBDATEST,
        username="lt_user",
        access_key="lt_key",
    )
    runner = CloudRunner(config)
    url = runner.build_remote_url()
    caps = runner.build_capabilities()

    assert "lt_user:lt_key@hub.lambdatest.com" in url
    assert "LT:Options" in caps


def test_cloud_runner_flag_disabled(monkeypatch):
    monkeypatch.delenv("NORMA_FEATURE_EXECUTION_CLOUD", raising=False)
    runner = CloudRunner()
    with pytest.raises(PermissionError, match="Cloud runner execution is disabled"):
        runner.create_session()


def test_cloud_runner_flag_enabled(monkeypatch):
    monkeypatch.setenv("NORMA_FEATURE_EXECUTION_CLOUD", "true")
    config = CloudConfig(username="user", access_key="key")
    runner = CloudRunner(config)
    session = runner.create_session()

    assert session["status"] == "READY"
    assert session["provider"] == "BROWSERSTACK"
