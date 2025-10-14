import json
import os
import tempfile

import pytest

from main import load_data


def test_load_data_success():
    """Test successful loading of JSON data."""
    test_data = {"key": "value", "number": 42}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        json.dump(test_data, f)
        temp_path = f.name

    try:
        result = load_data(temp_path)
        assert result == test_data
    finally:
        os.unlink(temp_path)


def test_load_data_file_not_found():
    """Test handling of missing file."""
    with pytest.raises(SystemExit):
        load_data("nonexistent_file.json")


def test_load_data_invalid_json():
    """Test handling of invalid JSON."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False
    ) as f:
        f.write("invalid json content")
        temp_path = f.name

    try:
        with pytest.raises(SystemExit):
            load_data(temp_path)
    finally:
        os.unlink(temp_path)
