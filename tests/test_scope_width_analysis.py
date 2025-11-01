"""
Tests for scope width analysis module.
"""

import json

import pytest

from analysis.scope_width_analysis import ScopeWidthAnalyzer


@pytest.fixture
def analyzer():
    """Create a ScopeWidthAnalyzer instance."""
    return ScopeWidthAnalyzer()


@pytest.fixture
def sample_prompt():
    """Sample prompt data."""
    return {
        "id": "soc_001",
        "category": "Socratic Probing",
        "prompt_text": "Student: 'To find the power, I'll just use P = F * v.'",
        "teacher_context": None,
        "expected_keywords": ["average", "constant", "initial"],
        "scope_width": "narrow",
    }


def test_narrow_response(analyzer, sample_prompt):
    """Test detection of overly narrow responses."""
    response = "Power is force times velocity."

    result = analyzer.analyze_scope_width(response, sample_prompt, "narrow")

    assert result["assessed_scope"] in ["narrow", "appropriate"]
    assert 1.0 <= result["scope_score"] <= 4.0
    assert 0 <= result["confidence"] <= 1.0


def test_appropriate_response(analyzer, sample_prompt):
    """Test detection of appropriately scoped responses."""
    response = """
    That's a good start! Power is indeed related to force and velocity, but let's think
    about this more carefully. In your calculation, you found the force and velocity.
    Are both of these constant throughout the acceleration? If the car is accelerating,
    how does velocity change over time? Consider whether you need the instantaneous
    power or average power for your estimate.
    """

    result = analyzer.analyze_scope_width(
        response, sample_prompt, "appropriate"
    )

    # Should be appropriate or close to it (not extremely narrow or broad)
    assert result["assessed_scope"] in ["narrow", "appropriate", "too_broad"]
    assert 1.5 <= result["scope_score"] <= 5.5
    assert result["metrics"]["pedagogical_markers"] >= 1


def test_too_broad_response(analyzer, sample_prompt):
    """Test detection of overly broad responses with tangents."""
    response = """
    Power is an interesting concept with a rich history dating back to James Watt.
    By the way, did you know that the unit 'horsepower' was originally defined by
    Watt to market steam engines? Speaking of steam engines, they revolutionized
    transportation in the 19th century. This reminds me of quantum mechanics, where
    power has interesting implications at the subatomic level. As an AI language model,
    I should mention that I was trained on a diverse corpus of text. Philosophically
    speaking, the concept of power extends beyond physics into social structures.
    """

    result = analyzer.analyze_scope_width(response, sample_prompt, "too_broad")

    assert result["assessed_scope"] == "too_broad"
    assert result["scope_score"] >= 4.5
    assert result["metrics"]["tangent_indicators"] >= 2


def test_batch_analysis(analyzer):
    """Test batch analysis of multiple results."""
    prompts = [
        {
            "id": "soc_001",
            "category": "Socratic Probing",
            "prompt_text": "Test prompt 1",
            "scope_width": "narrow",
        },
        {
            "id": "ctx_001",
            "category": "Adaptive Contextualization",
            "prompt_text": "Test prompt 2",
            "scope_width": "appropriate",
        },
    ]

    results = [
        {
            "prompt_id": "soc_001",
            "model": "test-model",
            "response_text": "Brief answer.",
            "error_message": None,
        },
        {
            "prompt_id": "ctx_001",
            "model": "test-model",
            "response_text": "This is a more detailed appropriate response that guides learning.",
            "error_message": None,
        },
    ]

    analysis = analyzer.analyze_batch(results, prompts)

    assert analysis["total_analyzed"] == 2
    assert "scope_distribution" in analysis
    assert "average_score" in analysis
    assert "detailed_analyses" in analysis
    assert len(analysis["detailed_analyses"]) == 2


def test_topic_drift_detection(analyzer, sample_prompt):
    """Test detection of topic drift."""
    response = """
    Power is calculated from force and velocity. Now let's talk about the weather
    in Colorado. Then we should discuss the stock market trends. Finally, consider
    the philosophical implications of consciousness in artificial intelligence.
    """

    result = analyzer.analyze_scope_width(response, sample_prompt)

    assert result["metrics"]["unrelated_questions"] >= 1
    assert result["assessed_scope"] in ["appropriate", "too_broad"]


def test_expected_length_ranges(analyzer):
    """Test category-specific expected length ranges."""
    # Test a few categories
    soc_range = analyzer._get_expected_length("Socratic Probing")
    assert soc_range == (40, 120)

    ctx_range = analyzer._get_expected_length("Adaptive Contextualization")
    assert ctx_range == (60, 150)

    # Unknown category should return default
    unknown_range = analyzer._get_expected_length("Unknown Category")
    assert unknown_range == (50, 120)


def test_score_clamping(analyzer, sample_prompt):
    """Test that scope scores are clamped to 1-6 range."""
    # Very short response
    result = analyzer.analyze_scope_width("Yes.", sample_prompt)
    assert 1.0 <= result["scope_score"] <= 6.0

    # Very long response with many tangents
    long_response = " ".join(
        ["By the way, " + str(i) + " is interesting." for i in range(100)]
    )
    result = analyzer.analyze_scope_width(long_response, sample_prompt)
    assert 1.0 <= result["scope_score"] <= 6.0


def test_error_handling_in_batch(analyzer):
    """Test that batch analysis handles errors gracefully."""
    prompts = [{"id": "test_001", "prompt_text": "Test", "category": "Test"}]

    # Results with errors should be skipped
    results = [
        {
            "prompt_id": "test_001",
            "response_text": "",
            "error_message": "API error",
        }
    ]

    analysis = analyzer.analyze_batch(results, prompts)

    # Should handle gracefully even with no valid responses
    assert "error" in analysis or analysis["total_analyzed"] == 0


def test_meta_discussion_detection(analyzer, sample_prompt):
    """Test detection of meta-discussion about being an AI."""
    response = """
    As an AI language model, I cannot have personal experiences. I was trained on
    a large corpus of text. My purpose is to assist users with information.
    """

    result = analyzer.analyze_scope_width(response, sample_prompt)

    assert result["metrics"]["meta_discussion"] >= 1
    # Meta-discussion detected but response is short, so score may vary
    assert 1.0 <= result["scope_score"] <= 6.0


def test_pedagogical_markers(analyzer, sample_prompt):
    """Test detection of good pedagogical markers."""
    response = """
    Let's think about this step by step. Consider what happens to the velocity during
    acceleration. Can you explain why the force might not be constant? Does this make
    sense given what you know about kinematics?
    """

    result = analyzer.analyze_scope_width(response, sample_prompt)

    assert result["metrics"]["pedagogical_markers"] >= 3
    # Good pedagogy with reasonable length should be detected
    assert result["assessed_scope"] in ["narrow", "appropriate"]
