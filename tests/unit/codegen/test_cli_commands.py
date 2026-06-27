import importlib
import sys
import types

from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch

# Stub behave import if the environment does not have it installed.
behave_module = types.ModuleType("behave")
behave_parser = types.ModuleType("behave.parser")
behave_parser.parse_feature = lambda *args, **kwargs: None
behave_model = types.ModuleType("behave.model")
behave_model.Feature = object
behave_model.Scenario = object
behave_model.Step = object
behave_module.parser = behave_parser
behave_module.model = behave_model
sys.modules["behave"] = behave_module
sys.modules["behave.parser"] = behave_parser
sys.modules["behave.model"] = behave_model

cli = importlib.import_module("antinode_norma.codegen.cli.commands").cli
CodegenConfig = importlib.import_module(
    "antinode_norma.codegen.config").CodegenConfig


class TestCodegenCLIParallelGeneration:
    @patch("antinode_norma.codegen.cli.commands.load_config")
    @patch("antinode_norma.codegen.cli.commands.Orchestrator")
    def test_generate_multiple_features_in_parallel(
            self, mock_orchestrator_cls, mock_load_config):
        config = CodegenConfig()
        config.default_framework = "playwright"
        config.output_dir = Path("generated_tests")
        config.quality.use_page_objects = False
        config.quality.generate_step_defs = False
        config.quality.enable_visual_testing = False
        mock_load_config.return_value = config

        mock_orch = mock_orchestrator_cls.return_value
        mock_orch.generate.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("login.feature").write_text("Feature: Login")
            Path("checkout.feature").write_text("Feature: Checkout")

            result = runner.invoke(
                cli,
                [
                    "generate",
                    "-f",
                    "login.feature",
                    "-f",
                    "checkout.feature",
                    "--workers",
                    "2",
                ],
            )

        assert result.exit_code == 0
        assert mock_orchestrator_cls.call_count >= 1
        assert mock_orch.generate.call_count == 2
        assert "Generated tests for 'login.feature'" in result.output
        assert "Generated tests for 'checkout.feature'" in result.output

    @patch("antinode_norma.codegen.cli.commands.load_config")
    @patch("antinode_norma.codegen.cli.commands.Orchestrator")
    def test_generate_single_feature_still_works(
            self, mock_orchestrator_cls, mock_load_config):
        config = CodegenConfig()
        config.default_framework = "playwright"
        config.output_dir = Path("generated_tests")
        config.quality.use_page_objects = False
        config.quality.generate_step_defs = False
        config.quality.enable_visual_testing = False
        mock_load_config.return_value = config

        mock_orch = mock_orchestrator_cls.return_value
        mock_orch.generate.return_value = None

        runner = CliRunner()
        with runner.isolated_filesystem():
            Path("login.feature").write_text("Feature: Login")
            result = runner.invoke(cli, ["generate", "-f", "login.feature"])

        assert result.exit_code == 0
        assert mock_orch.generate.call_count == 1
        assert "Tests generated successfully for 'login.feature'" in result.output
