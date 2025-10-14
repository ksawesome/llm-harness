"""Test imports and module structure."""

import pytest


def test_core_module_imports():
    """Test that all core modules can be imported."""
    modules_to_test = [
        "main",
        "models_config",
        "prompt_utils",
        "database",
        "manage_results",
        "utils.mock_provider",
        "utils.result_loader",
        "analysis.generate_report",
        "analysis.statistical_test",
        "analysis.llm_judge_evaluation",
        "analysis.comparative_analysis",
        "web.web_ui",
        "web.dashboard",
    ]

    for module_name in modules_to_test:
        try:
            __import__(module_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {module_name}: {e}")


def test_adapter_imports():
    """Test that all adapter modules can be imported."""
    adapters_to_test = [
        "adapters.openai_adapter",
        "adapters.anthropic_adapter",
        "adapters.google_adapter",
        "adapters.cohere_adapter",
        "adapters.huggingface_adapter",
    ]

    for adapter_name in adapters_to_test:
        try:
            __import__(adapter_name)
        except ImportError as e:
            pytest.fail(f"Failed to import {adapter_name}: {e}")


def test_adapter_functions_exist():
    """Test that adapter functions exist and are callable."""
    from adapters.anthropic_adapter import call_anthropic_api
    from adapters.cohere_adapter import call_cohere_api
    from adapters.google_adapter import call_google_api
    from adapters.huggingface_adapter import call_huggingface_api
    from adapters.openai_adapter import call_openai_api

    adapter_functions = [
        call_openai_api,
        call_anthropic_api,
        call_google_api,
        call_cohere_api,
        call_huggingface_api,
    ]

    for func in adapter_functions:
        assert callable(func), f"{func.__name__} is not callable"


def test_models_config_structure():
    """Test that models_config has expected structure."""
    from models_config import models_to_test

    assert isinstance(models_to_test, dict), "models_to_test should be a dict"
    assert len(models_to_test) > 0, "models_to_test should not be empty"

    # Check that each model has required attributes
    for model_name, config in models_to_test.items():
        assert hasattr(config, "name"), f"Model {model_name} missing name"
        assert hasattr(
            config, "adapter"
        ), f"Model {model_name} missing adapter"
        assert hasattr(
            config, "rate_limit_seconds"
        ), f"Model {model_name} missing rate_limit_seconds"
        assert hasattr(
            config, "timeout_seconds"
        ), f"Model {model_name} missing timeout_seconds"
        assert callable(
            config.adapter
        ), f"Model {model_name} adapter is not callable"


def test_mock_provider_structure():
    """Test that mock_provider has expected functions."""
    from utils.mock_provider import (
        _load_prompts,
        call_mock_api,
        ensure_synthetic_runs,
    )

    # Test function existence
    assert callable(call_mock_api)
    assert callable(ensure_synthetic_runs)
    assert callable(_load_prompts)

    # Test basic functionality
    result = call_mock_api("openai", "gpt-4", "test prompt", "")
    assert isinstance(result, dict)
    assert "response_text" in result
    assert "latency_ms" in result


def test_web_ui_structure():
    """Test that web UI modules have required structure."""
    import web.dashboard
    import web.web_ui

    # Check that Flask app exists
    assert hasattr(web.web_ui, "app")
    assert hasattr(web.dashboard, "app")

    # Check for route decorators (at least 'route' should exist)
    assert hasattr(web.web_ui.app, "route")
    assert hasattr(web.dashboard.app, "route")


def test_analysis_modules_structure():
    """Test that analysis modules have required functions."""
    from analysis.generate_report import BenchmarkReportGenerator
    from analysis.llm_judge_evaluation import LLMJudgeEvaluator
    from analysis.statistical_test import (
        analyze_inter_rater_reliability,
        analyze_model_performance,
    )

    # Test classes/functions exist
    assert callable(BenchmarkReportGenerator)
    assert callable(analyze_inter_rater_reliability)
    assert callable(analyze_model_performance)
    assert callable(LLMJudgeEvaluator)


def test_database_structure():
    """Test that database module has required structure."""
    from database import BenchmarkDatabase

    assert callable(BenchmarkDatabase)

    # Test basic instantiation (should not require actual DB file)
    db = BenchmarkDatabase(":memory:")
    assert hasattr(db, "store_benchmark_run")
    assert hasattr(db, "get_runs")
    assert hasattr(db, "get_results")


def test_prompt_utils_structure():
    """Test that prompt_utils has required functions."""
    from prompt_utils import (
        add_helm_style_prompts,
        expand_prompts_with_templates,
        load_system_prompts,
        load_test_prompts,
    )

    required_functions = [
        load_test_prompts,
        load_system_prompts,
        expand_prompts_with_templates,
        add_helm_style_prompts,
    ]

    for func in required_functions:
        assert callable(func)


def test_result_loader_structure():
    """Test that result_loader has required functions."""
    from utils.result_loader import STANDARD_COLUMNS, load_results

    assert callable(load_results)
    assert isinstance(STANDARD_COLUMNS, list)
    assert len(STANDARD_COLUMNS) > 0
