"""
Prompt utilities for the LLM benchmarking harness.
Handles loading, validation, and templating of prompts.
"""

import json
import os
from typing import Dict, List, Any, Optional
from jinja2 import Template, TemplateError
from jsonschema import validate, ValidationError, SchemaError


# JSON Schemas for validation
TEST_PROMPTS_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string", "pattern": "^[a-z]{3}_[0-9]{3}$"},
            "category": {"type": "string"},
            "prompt_text": {"type": "string"},
            "teacher_context": {"type": ["string", "null"]},
            "expected_keywords": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["id", "category", "prompt_text", "expected_keywords"],
        "additionalProperties": False,
    },
}

SYSTEM_PROMPTS_SCHEMA = {
    "type": "object",
    "patternProperties": {"^[a-z_]+$": {"type": "string"}},
    "additionalProperties": False,
}


def validate_json_data(
    data: Any, schema: Dict[str, Any], filename: str
) -> None:
    """
    Validate JSON data against a schema.

    Args:
        data: The JSON data to validate
        schema: The JSON schema to validate against
        filename: Name of the file for error messages

    Raises:
        ValidationError: If validation fails
        SchemaError: If schema is invalid
    """
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        raise ValidationError(
            f"Validation error in {filename}: {e.message} at {e.absolute_path}"
        )
    except SchemaError as e:
        raise SchemaError(f"Schema error in {filename}: {e.message}")


def load_and_validate_prompts(
    prompts_file: str, schema: Dict[str, Any]
) -> Any:
    """
    Load and validate prompts from a JSON file.

    Args:
        prompts_file: Path to the JSON file
        schema: JSON schema for validation

    Returns:
        Validated prompt data

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        ValidationError: If data doesn't match schema
    """
    if not os.path.exists(prompts_file):
        raise FileNotFoundError(f"Prompts file not found: {prompts_file}")

    with open(prompts_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    validate_json_data(data, schema, os.path.basename(prompts_file))
    return data


def load_test_prompts(prompts_file: str) -> List[Dict[str, Any]]:
    """
    Load and validate test prompts.

    Args:
        prompts_file: Path to test_prompts.json

    Returns:
        List of validated test prompt dictionaries
    """
    return load_and_validate_prompts(prompts_file, TEST_PROMPTS_SCHEMA)


def load_system_prompts(prompts_file: str) -> Dict[str, str]:
    """
    Load and validate system prompts.

    Args:
        prompts_file: Path to system_prompts.json

    Returns:
        Dictionary of validated system prompt strings
    """
    return load_and_validate_prompts(prompts_file, SYSTEM_PROMPTS_SCHEMA)


def render_template(
    template_str: str, variables: Optional[Dict[str, Any]] = None
) -> str:
    """
    Render a Jinja2 template with variables.

    Args:
        template_str: The template string
        variables: Dictionary of variables to substitute

    Returns:
        Rendered template string

    Raises:
        TemplateError: If template rendering fails
    """
    if variables is None:
        variables = {}

    try:
        template = Template(template_str)
        return template.render(**variables)
    except TemplateError as e:
        raise TemplateError(f"Template rendering error: {e}")


def expand_prompts_with_templates(
    prompts: List[Dict[str, Any]],
    template_vars: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Expand prompts that contain Jinja2 templates.

    Args:
        prompts: List of prompt dictionaries
        template_vars: Variables to use for template rendering

    Returns:
        List of prompts with templates rendered
    """
    expanded_prompts = []

    for prompt in prompts:
        expanded_prompt = prompt.copy()

        # Render prompt_text if it contains templates
        if "prompt_text" in prompt and prompt["prompt_text"]:
            expanded_prompt["prompt_text"] = render_template(
                prompt["prompt_text"], template_vars
            )

        # Render teacher_context if it exists and contains templates
        if "teacher_context" in prompt and prompt["teacher_context"]:
            expanded_prompt["teacher_context"] = render_template(
                prompt["teacher_context"], template_vars
            )

        expanded_prompts.append(expanded_prompt)

    return expanded_prompts


def get_prompt_categories(prompts: List[Dict[str, Any]]) -> List[str]:
    """
    Get unique categories from prompts.

    Args:
        prompts: List of prompt dictionaries

    Returns:
        List of unique category names
    """
    return list(
        set(prompt.get("category", "uncategorized") for prompt in prompts)
    )


def filter_prompts_by_category(
    prompts: List[Dict[str, Any]], category: str
) -> List[Dict[str, Any]]:
    """
    Filter prompts by category.

    Args:
        prompts: List of prompt dictionaries
        category: Category to filter by

    Returns:
        Filtered list of prompts
    """
    return [p for p in prompts if p.get("category") == category]


def add_helm_style_prompts(
    base_prompts: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Add HELM-style prompts for broader evaluation coverage.
    HELM (Holistic Evaluation of Language Models) includes various scenarios.

    Args:
        base_prompts: Existing prompts to extend

    Returns:
        Extended list with additional HELM-style prompts
    """
    helm_prompts = [
        {
            "id": "helm_001",
            "category": "Commonsense Reasoning",
            "prompt_text": "If you have a glass of water and you pour half of it into another glass, how many glasses of water do you have?",
            "teacher_context": "This tests basic commonsense reasoning about quantities and containers.",
            "expected_keywords": ["two", "glasses", "water", "half"],
        },
        {
            "id": "helm_002",
            "category": "Mathematical Reasoning",
            "prompt_text": "A train leaves station A at 10:00 AM traveling at 60 mph towards station B, 300 miles away. Another train leaves station B at 11:00 AM traveling at 80 mph towards station A. When do they meet?",
            "teacher_context": "This requires understanding relative speeds and distance calculations.",
            "expected_keywords": ["time", "distance", "speed", "meet"],
        },
        {
            "id": "helm_003",
            "category": "Causal Reasoning",
            "prompt_text": "John put a metal spoon in a hot cup of coffee. After a few minutes, he touched the spoon and it was hot. Why was the spoon hot?",
            "teacher_context": "This tests understanding of heat transfer and causality.",
            "expected_keywords": ["heat", "transfer", "coffee", "conduction"],
        },
        {
            "id": "helm_004",
            "category": "Ethical Reasoning",
            "prompt_text": "You find a wallet with $500 and identification. The owner lives nearby. What should you do?",
            "teacher_context": "This evaluates ethical decision-making and moral reasoning.",
            "expected_keywords": ["return", "wallet", "owner", "honest"],
        },
    ]

    # Generate new IDs to avoid conflicts
    max_id = max(
        int(p["id"].split("_")[1]) for p in base_prompts if "_" in p["id"]
    )
    for prompt in helm_prompts:
        max_id += 1
        prompt["id"] = f"helm_{max_id:03d}"

    return base_prompts + helm_prompts
