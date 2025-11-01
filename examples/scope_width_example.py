#!/usr/bin/env python
"""
Example: Running Scope Width Analysis

This script demonstrates how to:
1. Load the 120-prompt bank
2. Run a benchmark (or load existing results)
3. Analyze scope width
4. Visualize results
"""

import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.scope_width_analysis import (
    ScopeWidthAnalyzer,
    analyze_results_file,
    load_prompts_with_scope,
)


def example_1_basic_analysis():
    """Example 1: Analyze a single response"""
    print("=" * 60)
    print("EXAMPLE 1: Basic Scope Width Analysis")
    print("=" * 60)

    analyzer = ScopeWidthAnalyzer()

    # Sample prompt
    prompt_data = {
        "id": "soc_001",
        "category": "Socratic Probing",
        "prompt_text": "Student: 'To find power, I'll use P = F * v'",
        "scope_width": "narrow",
    }

    # Sample response (too broad - includes tangents)
    response = """
    That's an interesting approach! Power calculations have a rich history dating back
    to James Watt. By the way, did you know that horsepower was originally defined
    to market steam engines? Speaking of engines, they revolutionized the industrial
    revolution. But let's think about your equation P = F * v. Are the force and
    velocity constant during acceleration?
    """

    result = analyzer.analyze_scope_width(response, prompt_data, "narrow")

    print(f"\nPrompt: {prompt_data['prompt_text']}")
    print(f"\nResponse (first 100 chars): {response[:100]}...")
    print(f"\nAnalysis Results:")
    print(f"  Assessed Scope: {result['assessed_scope']}")
    print(f"  Scope Score (1-6): {result['scope_score']}")
    print(f"  Confidence: {result['confidence']}")
    print(f"  Expected Scope: {result['expected_scope']}")
    print(f"  Matches Expected: {result['matches_expected']}")
    print(f"\nDetected Metrics:")
    for key, value in result["metrics"].items():
        print(f"  {key}: {value}")


def example_2_load_120_prompts():
    """Example 2: Load and explore the 120-prompt bank"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Exploring the 120-Prompt Bank")
    print("=" * 60)

    prompts = load_prompts_with_scope("data/test_prompts_120.json")

    print(f"\nTotal prompts: {len(prompts)}")

    # Count by category
    from collections import Counter

    categories = Counter(p["category"] for p in prompts)
    print("\nPrompts by Category:")
    for category, count in categories.most_common():
        print(f"  {category}: {count}")

    # Count by expected scope width
    scope_widths = Counter(p.get("scope_width", "unknown") for p in prompts)
    print("\nExpected Scope Width Distribution:")
    for scope, count in scope_widths.most_common():
        print(f"  {scope}: {count}")

    # Show a few examples
    print("\nSample Prompts:")
    for i, prompt in enumerate(prompts[:3]):
        print(f"\n  {i+1}. [{prompt['id']}] {prompt['category']}")
        print(f"     Scope: {prompt.get('scope_width', 'N/A')}")
        print(f"     Text: {prompt['prompt_text'][:80]}...")


def example_3_batch_analysis():
    """Example 3: Batch analysis simulation"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Batch Analysis Simulation")
    print("=" * 60)

    # Simulate some results
    simulated_results = [
        {
            "prompt_id": "soc_001",
            "model": "gpt-4",
            "response_text": "Consider whether force and velocity are constant during acceleration.",
            "error_message": None,
        },
        {
            "prompt_id": "ctx_001",
            "model": "gpt-4",
            "response_text": """
            Given the mass of 7kg and friction of 5N, you'll need to calculate the net force.
            The motor must overcome both the inertial resistance (F=ma) and the friction.
            Start by finding the total force required, then think about how that relates
            to the wheel torque given the 4-inch diameter.
            """,
            "error_message": None,
        },
        {
            "prompt_id": "edg_001",
            "model": "gpt-4",
            "response_text": """
            Let's focus on the Mettle engineering estimation problem. While moon gravity
            is interesting, the current task is about the electric car power calculation
            on Earth. For the jellybean estimation, that would be a separate Fermi
            estimation exercise. Let's return to calculating the motor power needed.
            """,
            "error_message": None,
        },
    ]

    prompts = [
        {
            "id": "soc_001",
            "category": "Socratic Probing",
            "prompt_text": "Test 1",
            "scope_width": "narrow",
        },
        {
            "id": "ctx_001",
            "category": "Adaptive Contextualization",
            "prompt_text": "Test 2",
            "scope_width": "appropriate",
        },
        {
            "id": "edg_001",
            "category": "Edge Cases & Adversarial",
            "prompt_text": "Test 3",
            "scope_width": "too_broad",
        },
    ]

    analyzer = ScopeWidthAnalyzer()
    analysis = analyzer.analyze_batch(simulated_results, prompts)

    print(f"\nBatch Analysis Results:")
    print(f"  Total Analyzed: {analysis['total_analyzed']}")
    print(f"  Average Score: {analysis['average_score']}")
    print(f"  Average Confidence: {analysis['average_confidence']}")

    print(f"\nScope Distribution:")
    dist = analysis["scope_distribution"]
    print(f"  Narrow: {dist['narrow_pct']}%")
    print(f"  Appropriate: {dist['appropriate_pct']}%")
    print(f"  Too Broad: {dist['too_broad_pct']}%")

    if analysis.get("accuracy"):
        print(f"\nAccuracy vs Expected: {analysis['accuracy']}%")

    # Show per-response details
    print("\nPer-Response Analysis:")
    for i, detail in enumerate(analysis["detailed_analyses"]):
        print(f"\n  Response {i+1} [{detail['prompt_id']}]:")
        print(f"    Assessed: {detail['assessed_scope']}")
        print(f"    Score: {detail['scope_score']}")
        print(f"    Expected: {detail['expected_scope']}")
        print(f"    Match: {'✓' if detail['matches_expected'] else '✗'}")


def example_4_real_file_analysis():
    """Example 4: Analyze a real CSV file (if available)"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Real File Analysis")
    print("=" * 60)

    # Check if any result files exist
    import glob

    result_files = glob.glob("results/raw_output/benchmark_results_*.csv")

    if not result_files:
        print("\nNo benchmark result files found in results/raw_output/")
        print("Run a benchmark first:")
        print("  python main.py --prompt-file data/test_prompts_120.json")
        return

    # Use most recent file
    latest_file = sorted(result_files)[-1]
    print(f"\nAnalyzing: {latest_file}")

    try:
        analysis = analyze_results_file(
            latest_file, "data/test_prompts_120.json"
        )
        print("\n✓ Analysis complete!")
        print(
            f"  Output saved to: {latest_file.replace('.csv', '_scope_width.json')}"
        )
    except Exception as e:
        print(f"\n✗ Error analyzing file: {e}")
        print(
            "Make sure the file contains 'response_text' and 'prompt_id' columns"
        )


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SCOPE WIDTH ANALYSIS EXAMPLES")
    print("=" * 60)

    example_1_basic_analysis()
    example_2_load_120_prompts()
    example_3_batch_analysis()
    example_4_real_file_analysis()

    print("\n" + "=" * 60)
    print("Examples complete!")
    print("=" * 60)
    print("\nNext steps:")
    print(
        "1. Run benchmark: python main.py --prompt-file data/test_prompts_120.json"
    )
    print(
        "2. Analyze results: python -m analysis.scope_width_analysis <results.csv>"
    )
    print(
        "3. Review human trial template: data/human_trials_google_form_template.md"
    )
    print()
