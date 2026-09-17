import os
from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from antinode_norma.core.features import FeatureFlagResolver


class CloudProvider(str, Enum):
    BROWSERSTACK = "BROWSERSTACK"
    SAUCELABS = "SAUCELABS"
    LAMBDATEST = "LAMBDATEST"


class CloudConfig(BaseModel):
    provider: CloudProvider = CloudProvider.BROWSERSTACK
    username: str = ""
    access_key: str = ""
    browser_name: str = "chrome"
    browser_version: str = "latest"
    os_name: str = "Windows"
    os_version: str = "10"
    extra_capabilities: Dict[str, Any] = Field(default_factory=dict)


class CloudRunner:
    def __init__(self, config: Optional[CloudConfig] = None):
        self.config = config or CloudConfig()

    def build_remote_url(self) -> str:
        provider = self.config.provider
        user = self.config.username or os.getenv(f"{provider.value}_USERNAME", "")
        key = self.config.access_key or os.getenv(f"{provider.value}_ACCESS_KEY", "")

        if provider == CloudProvider.BROWSERSTACK:
            return f"https://{user}:{key}@hub-cloud.browserstack.com/wd/hub"
        elif provider == CloudProvider.SAUCELABS:
            return f"https://{user}:{key}@ondemand.us-west-1.saucelabs.com:443/wd/hub"
        elif provider == CloudProvider.LAMBDATEST:
            return f"https://{user}:{key}@hub.lambdatest.com/wd/hub"
        else:
            raise ValueError(f"Unsupported cloud provider: {provider}")

    def build_capabilities(self) -> Dict[str, Any]:
        provider = self.config.provider
        caps: Dict[str, Any] = {
            "browserName": self.config.browser_name,
            "browserVersion": self.config.browser_version,
        }

        if provider == CloudProvider.BROWSERSTACK:
            caps["bstack:options"] = {
                "os": self.config.os_name,
                "osVersion": self.config.os_version,
                "projectName": "Norma BDD",
            }
        elif provider == CloudProvider.SAUCELABS:
            caps["sauce:options"] = {
                "platformName": f"{self.config.os_name} {self.config.os_version}",
                "name": "Norma BDD Execution",
            }
        elif provider == CloudProvider.LAMBDATEST:
            caps["LT:Options"] = {
                "platform": f"{self.config.os_name} {self.config.os_version}",
                "project": "Norma BDD",
            }

        caps.update(self.config.extra_capabilities)
        return caps

    def create_session(self) -> Dict[str, Any]:
        resolver = FeatureFlagResolver()
        if not resolver.is_enabled("execution_cloud"):
            raise PermissionError(
                "Cloud runner execution is disabled. Enable feature flag 'execution_cloud' in norma.config.yml or NORMA_FEATURE_EXECUTION_CLOUD=true."
            )

        return {
            "provider": self.config.provider.value,
            "remote_url": self.build_remote_url(),
            "capabilities": self.build_capabilities(),
            "status": "READY",
        }
