"""
Scope Width Analysis Module
Analyzes LLM responses for scope width appropriateness based on prompt categories.
"""

import json
import re
from typing import Dict, List, Optional, Tuple


class ScopeWidthAnalyzer:
    """
    Analyzes LLM responses to determine if they maintain appropriate scope width.

    Scope Width Categories:
    - narrow: Response is too minimal or unhelpfully brief
    - appropriate: Response maintains good pedagogical balance
    - too_broad: Response includes excessive tangents or off-topic content
    """

    def __init__(self):
        # Keywords indicating scope problems
        self.tangent_indicators = [
            "quantum mechanics",
            "history of",
            "philosophical",
            "by the way",
            "speaking of",
            "this reminds me",
            "interestingly",
            "fun fact",
            "did you know",
        ]

        self.meta_discussion_indicators = [
            "as an AI",
            "I am a language model",
            "I was trained",
            "my purpose is",
            "I cannot have opinions",
        ]

        # Keywords indicating pedagogically appropriate scope
        self.appropriate_indicators = [
            "consider",
            "think about",
            "what happens if",
            "does this make sense",
            "can you explain",
            "let's break this down",
        ]

    def analyze_scope_width(
        self,
        response: str,
        prompt_data: dict,
        expected_scope: str | None = None,
    ) -> dict[str, any]:
        """
        Analyze a response for scope width appropriateness.

        Args:
            response: The LLM's response text
            prompt_data: The original prompt data including category and context
            expected_scope: Expected scope from prompt data (narrow/appropriate/too_broad)

        Returns:
            Dictionary with scope width assessment and confidence score
        """
        response_lower = response.lower()

        # Calculate various metrics
        word_count = len(response.split())
        sentence_count = len(re.findall(r"[.!?]+", response))
        paragraph_count = len(response.split("\n\n"))

        tangent_count = sum(
            1
            for indicator in self.tangent_indicators
            if indicator in response_lower
        )

        meta_discussion_count = sum(
            1
            for indicator in self.meta_discussion_indicators
            if indicator in response_lower
        )

        appropriate_pedagogy_count = sum(
            1
            for indicator in self.appropriate_indicators
            if indicator in response_lower
        )

        # Detect multiple questions on unrelated topics
        unrelated_questions = self._detect_topic_drift(response, prompt_data)

        # Category-specific expectations
        category = prompt_data.get("category", "")
        expected_length_range = self._get_expected_length(category)

        # Scoring logic (0-6 scale matching human evaluation form)
        # 1-2: Too narrow, 3-4: Appropriate, 5-6: Too broad
        score = 3.5  # Start at neutral appropriate
        confidence = 0.5

        # Adjust based on length
        if word_count < expected_length_range[0]:
            score -= 1.5  # Likely too narrow
            confidence += 0.2
        elif word_count > expected_length_range[1] * 2:
            score += 1.5  # Likely too broad
            confidence += 0.2

        # Adjust for tangents and meta-discussion
        if tangent_count > 0:
            score += 0.5 * tangent_count
            confidence += 0.15

        if meta_discussion_count > 0:
            score += 0.3 * meta_discussion_count
            confidence += 0.1

        # Adjust for pedagogical appropriateness
        if appropriate_pedagogy_count >= 2:
            score -= 0.3  # Slightly more appropriate
            confidence += 0.1

        # Adjust for topic drift
        if unrelated_questions > 1:
            score += 1.0
            confidence += 0.2

        # Clamp score to 1-6 range
        score = max(1.0, min(6.0, score))
        confidence = min(1.0, confidence)

        # Determine category
        if score < 2.5:
            assessed_scope = "narrow"
        elif score < 4.5:
            assessed_scope = "appropriate"
        else:
            assessed_scope = "too_broad"

        return {
            "assessed_scope": assessed_scope,
            "scope_score": round(score, 2),
            "confidence": round(confidence, 2),
            "expected_scope": expected_scope,
            "matches_expected": (
                assessed_scope == expected_scope if expected_scope else None
            ),
            "metrics": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "tangent_indicators": tangent_count,
                "meta_discussion": meta_discussion_count,
                "pedagogical_markers": appropriate_pedagogy_count,
                "unrelated_questions": unrelated_questions,
            },
        }

    def _detect_topic_drift(self, response: str, prompt_data: dict) -> int:
        """
        Detect if response drifts to unrelated topics.
        Returns count of likely unrelated questions/topics addressed.
        """
        # Split into sentences
        sentences = re.split(r"[.!?]+", response)

        # Keywords from the prompt
        prompt_text = prompt_data.get("prompt_text", "").lower()
        prompt_keywords = set(re.findall(r"\b\w{4,}\b", prompt_text))

        # Core engineering terms expected in scope
        core_terms = {
            "power",
            "force",
            "energy",
            "torque",
            "velocity",
            "acceleration",
            "friction",
            "efficiency",
            "motor",
            "calculation",
            "equation",
        }

        unrelated_count = 0
        for sentence in sentences:
            sentence_lower = sentence.lower()
            sentence_keywords = set(re.findall(r"\b\w{4,}\b", sentence_lower))

            # Check if sentence has low overlap with prompt keywords and core terms
            overlap = len(sentence_keywords & (prompt_keywords | core_terms))

            if len(sentence_keywords) > 5 and overlap < 2:
                # Long sentence with minimal topical overlap - likely drift
                unrelated_count += 1

        return unrelated_count

    def _get_expected_length(self, category: str) -> tuple[int, int]:
        """
        Get expected word count range (min, max) for a prompt category.
        """
        length_expectations = {
            "Socratic Probing": (40, 120),
            "Adaptive Contextualization": (60, 150),
            "Feedback & Improvement": (50, 130),
            "Edge Cases & Adversarial": (30, 80),
            "Safety Challenges": (30, 80),
            "Template Examples": (50, 120),
        }
        return length_expectations.get(category, (50, 120))

    def analyze_batch(
        self, results: list[dict], prompts: list[dict]
    ) -> dict[str, any]:
        """
        Analyze scope width for a batch of results.

        Args:
            results: List of result dictionaries with response_text and prompt_id
            prompts: List of prompt data dictionaries

        Returns:
            Dictionary with aggregated analysis across all results
        """
        prompt_lookup = {p["id"]: p for p in prompts}

        analyses = []
        for result in results:
            prompt_data = prompt_lookup.get(result.get("prompt_id"))
            if not prompt_data:
                continue

            expected_scope = prompt_data.get("scope_width")
            response_text = result.get("response_text", "")

            if not response_text or result.get("error_message"):
                continue

            analysis = self.analyze_scope_width(
                response_text, prompt_data, expected_scope
            )

            analyses.append(
                {
                    "prompt_id": result["prompt_id"],
                    "model": result.get("model"),
                    **analysis,
                }
            )

        # Aggregate statistics
        if not analyses:
            return {
                "error": "No valid responses to analyze",
                "total_analyzed": 0,
                "scope_distribution": {
                    "narrow": 0,
                    "appropriate": 0,
                    "too_broad": 0,
                    "narrow_pct": 0.0,
                    "appropriate_pct": 0.0,
                    "too_broad_pct": 0.0,
                },
                "average_score": 0.0,
                "average_confidence": 0.0,
                "accuracy": None,
                "detailed_analyses": [],
            }

        total = len(analyses)
        narrow_count = sum(
            1 for a in analyses if a["assessed_scope"] == "narrow"
        )
        appropriate_count = sum(
            1 for a in analyses if a["assessed_scope"] == "appropriate"
        )
        too_broad_count = sum(
            1 for a in analyses if a["assessed_scope"] == "too_broad"
        )

        avg_score = sum(a["scope_score"] for a in analyses) / total
        avg_confidence = sum(a["confidence"] for a in analyses) / total

        # Accuracy if expected scope is provided
        matches = sum(1 for a in analyses if a["matches_expected"])
        accuracy = matches / total if matches > 0 else None

        return {
            "total_analyzed": total,
            "scope_distribution": {
                "narrow": narrow_count,
                "appropriate": appropriate_count,
                "too_broad": too_broad_count,
                "narrow_pct": round(narrow_count / total * 100, 1),
                "appropriate_pct": round(appropriate_count / total * 100, 1),
                "too_broad_pct": round(too_broad_count / total * 100, 1),
            },
            "average_score": round(avg_score, 2),
            "average_confidence": round(avg_confidence, 2),
            "accuracy": round(accuracy * 100, 1) if accuracy else None,
            "detailed_analyses": analyses,
        }


def load_prompts_with_scope(
    prompt_file: str = "data/test_prompts_120.json",
) -> list[dict]:
    """Load prompts from JSON file."""
    with open(prompt_file, encoding="utf-8") as f:
        return json.load(f)


def analyze_results_file(
    results_csv: str, prompts_json: str = "data/test_prompts_120.json"
):
    """
    Analyze scope width for all results in a CSV file.

    Args:
        results_csv: Path to benchmark results CSV
        prompts_json: Path to prompts JSON file
    """
    import pandas as pd

    # Load data
    prompts = load_prompts_with_scope(prompts_json)
    results_df = pd.read_csv(results_csv)

    # Convert to list of dicts for analysis
    results = results_df.to_dict("records")

    # Run analysis
    analyzer = ScopeWidthAnalyzer()
    analysis = analyzer.analyze_batch(results, prompts)

    # Print summary
    print("\n=== Scope Width Analysis ===")
    print(f"Total responses analyzed: {analysis['total_analyzed']}")
    print(f"Average scope score (1-6): {analysis['average_score']}")
    print(f"Average confidence: {analysis['average_confidence']}")
    print("\nScope Distribution:")
    print(
        f"  Narrow (too minimal): {analysis['scope_distribution']['narrow_pct']}%"
    )
    print(
        f"  Appropriate: {analysis['scope_distribution']['appropriate_pct']}%"
    )
    print(
        f"  Too Broad (tangents): {analysis['scope_distribution']['too_broad_pct']}%"
    )

    if analysis.get("accuracy"):
        print(f"\nAccuracy vs expected scope: {analysis['accuracy']}%")

    return analysis


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python -m analysis.scope_width_analysis <results_csv> [prompts_json]"
        )
        print(
            "Example: python -m analysis.scope_width_analysis results/raw_output/benchmark_results_20251013.csv"
        )
        sys.exit(1)

    results_file = sys.argv[1]
    prompts_file = (
        sys.argv[2] if len(sys.argv) > 2 else "data/test_prompts_120.json"
    )

    analysis = analyze_results_file(results_file, prompts_file)

    # Save detailed analysis
    output_file = results_file.replace(".csv", "_scope_width.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)
    print(f"\nDetailed analysis saved to: {output_file}")
