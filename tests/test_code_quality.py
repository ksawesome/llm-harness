import os
import subprocess
import sys


def test_black_formatting():
    """Test that all Python files are properly formatted with black."""
    # Get the directory of this test file
    test_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(test_dir)

    # Run black --check on the project
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", project_root],
        capture_output=True,
        text=True,
        cwd=project_root,
    )

    # Black returns 0 if no changes needed, 1 if changes would be made, 123 if error
    if result.returncode == 1:
        # Print the diff for debugging
        print("Black formatting issues found:")
        print(result.stdout)
        print(result.stderr)
        assert (
            False
        ), "Code is not properly formatted with black. Run 'black .' to fix."
    elif result.returncode == 123:
        print("Black error:")
        print(result.stderr)
        assert False, f"Black failed with error: {result.stderr}"
    else:
        # returncode 0 means all good
        assert (
            result.returncode == 0
        ), f"Unexpected black return code: {result.returncode}"


def test_flake8_linting():
    """Test that all Python files pass flake8 linting."""
    # Get the directory of this test file
    test_dir = os.path.dirname(__file__)
    project_root = os.path.dirname(test_dir)

    # Run flake8 on the project
    result = subprocess.run(
        [sys.executable, "-m", "flake8", project_root],
        capture_output=True,
        text=True,
        cwd=project_root,
    )

    if result.returncode != 0:
        print("Flake8 linting issues found:")
        print(result.stdout)
        print(result.stderr)
        assert False, "Code has linting issues. Fix flake8 errors."

    assert (
        result.returncode == 0
    ), f"Flake8 failed with return code: {result.returncode}"
