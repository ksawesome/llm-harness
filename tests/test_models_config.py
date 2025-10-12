from models_config import ModelConfig, models_to_test


def test_model_config_validation():
    """Test that ModelConfig validates correctly."""
    config = ModelConfig(
        name="test-model",
        adapter=lambda: None,  # Dummy adapter
        rate_limit_seconds=5.0,
        timeout_seconds=60,
        temperature=0.5,
    )
    assert config.name == "test-model"
    assert config.rate_limit_seconds == 5.0
    assert config.timeout_seconds == 60
    assert config.temperature == 0.5


def test_models_to_test_structure():
    """Test that models_to_test has expected structure."""
    assert isinstance(models_to_test, dict)
    assert len(models_to_test) > 0
    for key, config in models_to_test.items():
        assert isinstance(config, ModelConfig)
        assert config.name == key
        assert callable(config.adapter)
