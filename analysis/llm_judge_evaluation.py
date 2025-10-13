"""
LLM-as-Judge Evaluation System
Uses a powerful LLM (like GPT-4) to evaluate and score responses from other models.
"""

import pandas as pd
import asyncio
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from adapters import call_openai_api


@dataclass
class EvaluationResult:
    """Result of LLM-as-judge evaluation."""

    model_name: str
    prompt: str
    response: str
    score: float
    reasoning: str
    criteria_scores: Dict[str, float]
    judge_model: str
    timestamp: str


class LLMJudgeEvaluator:
    """Evaluates model responses using LLM-as-judge methodology."""

    def __init__(
        self, judge_model: str = "gpt-4", judge_api_key: Optional[str] = None
    ):
        """
        Initialize the LLM judge evaluator.

        Args:
            judge_model: Model to use as judge (default: gpt-4)
            judge_api_key: API key for judge model (uses environment if not provided)
        """
        self.judge_model = judge_model
        self.judge_api_key = judge_api_key or os.getenv("OPENAI_API_KEY")

        if not self.judge_api_key:
            raise ValueError(
                "Judge API key not provided and OPENAI_API_KEY not set"
            )

        # Initialize judge adapter (using function-based approach)
        self.judge_adapter = None  # We'll call the function directly

        # Evaluation criteria
        self.criteria = {
            "relevance": "How relevant is the response to the prompt?",
            "accuracy": "How accurate and factual is the response?",
            "completeness": "How complete is the response in addressing the prompt?",
            "clarity": "How clear and understandable is the response?",
            "helpfulness": "How helpful is the response to the user?",
        }

    def create_evaluation_prompt(
        self, original_prompt: str, model_response: str
    ) -> str:
        """Create the evaluation prompt for the judge LLM."""
        criteria_text = "\n".join(
            [
                f"- {name}: {description}"
                for name, description in self.criteria.items()
            ]
        )

        evaluation_prompt = f"""
You are an expert evaluator of AI model responses. Your task is to evaluate the quality of a response to a given prompt.

**Original Prompt:**
{original_prompt}

**Model Response:**
{model_response}

**Evaluation Criteria:**
{criteria_text}

**Instructions:**
1. Evaluate the response on each criterion using a scale of 1-10 (1 = very poor, 10 = excellent)
2. Provide a brief reasoning for each score
3. Calculate an overall score (average of all criteria)
4. Be consistent, fair, and objective in your evaluation

**Output Format:**
Provide your evaluation in the following JSON format:
{{
    "overall_score": <number>,
    "criteria_scores": {{
        "relevance": <number>,
        "accuracy": <number>,
        "completeness": <number>,
        "clarity": <number>,
        "helpfulness": <number>
    }},
    "reasoning": "<brief explanation of the overall evaluation>"
}}

**Important:** Only output valid JSON. Do not include any other text.
"""

        return evaluation_prompt.strip()

    async def evaluate_single_response(
        self, prompt: str, response: str, model_name: str
    ) -> EvaluationResult:
        """Evaluate a single model response."""
        evaluation_prompt = self.create_evaluation_prompt(prompt, response)

        try:
            # Get evaluation from judge model
            judge_result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: call_openai_api(
                    self.judge_model,
                    evaluation_prompt,
                    "You are an expert evaluator. Provide your response as valid JSON only.",
                ),
            )

            judge_response = judge_result.get("response_text", "")

            # Parse JSON response
            try:
                evaluation_data = json.loads(judge_response.strip())
            except json.JSONDecodeError:
                # Fallback parsing if JSON is malformed
                evaluation_data = self._parse_fallback_evaluation(
                    judge_response
                )

            # Create evaluation result
            result = EvaluationResult(
                model_name=model_name,
                prompt=prompt,
                response=response,
                score=evaluation_data.get("overall_score", 0.0),
                reasoning=evaluation_data.get(
                    "reasoning", "No reasoning provided"
                ),
                criteria_scores=evaluation_data.get("criteria_scores", {}),
                judge_model=self.judge_model,
                timestamp=datetime.now().isoformat(),
            )

            return result

        except Exception as e:
            # Return failed evaluation
            return EvaluationResult(
                model_name=model_name,
                prompt=prompt,
                response=response,
                score=0.0,
                reasoning=f"Evaluation failed: {str(e)}",
                criteria_scores={},
                judge_model=self.judge_model,
                timestamp=datetime.now().isoformat(),
            )

    def _parse_fallback_evaluation(self, response: str) -> Dict:
        """Fallback parsing for malformed JSON responses."""
        # Try to extract scores from text
        scores = {}
        overall_score = 5.0  # Default

        try:
            # Look for overall score
            if "overall_score" in response:
                import re

                score_match = re.search(
                    r'"overall_score"\s*:\s*(\d+(?:\.\d+)?)', response
                )
                if score_match:
                    overall_score = float(score_match.group(1))

            # Look for criteria scores
            for criterion in self.criteria.keys():
                score_match = re.search(
                    f'"{criterion}"\\s*:\\s*(\\d+(?:\\.\\d+)?)', response
                )
                if score_match:
                    scores[criterion] = float(score_match.group(1))
                else:
                    scores[criterion] = overall_score

        except Exception:
            # If all parsing fails, assign default scores
            scores = {
                criterion: overall_score for criterion in self.criteria.keys()
            }

        return {
            "overall_score": overall_score,
            "criteria_scores": scores,
            "reasoning": "Parsed from malformed response",
        }

    async def evaluate_responses_batch(
        self,
        responses_df: pd.DataFrame,
        prompt_column: str = "prompt",
        response_column: str = "response",
        model_column: str = "model",
    ) -> List[EvaluationResult]:
        """
        Evaluate a batch of responses.

        Args:
            responses_df: DataFrame containing responses to evaluate
            prompt_column: Column name for prompts
            response_column: Column name for responses
            model_column: Column name for model names

        Returns:
            List of evaluation results
        """
        tasks = []

        for _, row in responses_df.iterrows():
            if pd.notna(row[response_column]) and row[response_column].strip():
                task = self.evaluate_single_response(
                    prompt=str(row[prompt_column]),
                    response=str(row[response_column]),
                    model_name=str(row[model_column]),
                )
                tasks.append(task)

        # Execute evaluations concurrently
        print(f"Evaluating {len(tasks)} responses using {self.judge_model}...")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions and return successful results
        successful_results = []
        for result in results:
            if isinstance(result, EvaluationResult):
                successful_results.append(result)
            else:
                print(f"Evaluation failed: {result}")

        return successful_results

    def save_evaluation_results(
        self, results: List[EvaluationResult], output_path: str
    ):
        """Save evaluation results to JSON file."""
        results_data = []
        for result in results:
            result_dict = {
                "model_name": result.model_name,
                "prompt": result.prompt,
                "response": result.response,
                "score": result.score,
                "reasoning": result.reasoning,
                "criteria_scores": result.criteria_scores,
                "judge_model": result.judge_model,
                "timestamp": result.timestamp,
            }
            results_data.append(result_dict)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print(f"Saved {len(results)} evaluation results to {output_path}")

    def load_evaluation_results(
        self, input_path: str
    ) -> List[EvaluationResult]:
        """Load evaluation results from JSON file."""
        with open(input_path, "r", encoding="utf-8") as f:
            results_data = json.load(f)

        results = []
        for data in results_data:
            result = EvaluationResult(
                model_name=data["model_name"],
                prompt=data["prompt"],
                response=data["response"],
                score=data["score"],
                reasoning=data["reasoning"],
                criteria_scores=data["criteria_scores"],
                judge_model=data["judge_model"],
                timestamp=data["timestamp"],
            )
            results.append(result)

        return results

    def generate_evaluation_summary(
        self, results: List[EvaluationResult]
    ) -> Dict:
        """Generate summary statistics from evaluation results."""
        if not results:
            return {}

        df = pd.DataFrame(
            [
                {"model": r.model_name, "score": r.score, **r.criteria_scores}
                for r in results
            ]
        )

        summary = {}

        # Overall statistics
        summary["total_evaluations"] = len(results)
        summary["models_evaluated"] = df["model"].nunique()
        summary["judge_model"] = results[0].judge_model if results else None

        # Per-model statistics
        model_stats = []
        for model in df["model"].unique():
            model_df = df[df["model"] == model]
            stats = {
                "model": model,
                "evaluations": len(model_df),
                "avg_score": model_df["score"].mean(),
                "median_score": model_df["score"].median(),
                "std_score": model_df["score"].std(),
                "min_score": model_df["score"].min(),
                "max_score": model_df["score"].max(),
            }

            # Add criteria averages
            for criterion in self.criteria.keys():
                if criterion in model_df.columns:
                    stats[f"avg_{criterion}"] = model_df[criterion].mean()

            model_stats.append(stats)

        summary["model_stats"] = sorted(
            model_stats, key=lambda x: x["avg_score"], reverse=True
        )
        return summary


async def main():
    """Main function for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="LLM-as-Judge Evaluation System"
    )
    parser.add_argument(
        "csv_path", help="Path to CSV file containing model responses"
    )
    parser.add_argument(
        "--judge-model", default="gpt-4", help="Model to use as judge"
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Output directory for evaluation results",
    )
    parser.add_argument(
        "--prompt-column", default="prompt", help="Column name for prompts"
    )
    parser.add_argument(
        "--response-column",
        default="response",
        help="Column name for responses",
    )
    parser.add_argument(
        "--model-column", default="model", help="Column name for model names"
    )

    args = parser.parse_args()

    # Load responses
    print(f"Loading responses from {args.csv_path}")
    df = pd.read_csv(args.csv_path)

    # Initialize evaluator
    evaluator = LLMJudgeEvaluator(judge_model=args.judge_model)

    # Evaluate responses
    results = await evaluator.evaluate_responses_batch(
        df,
        prompt_column=args.prompt_column,
        response_column=args.response_column,
        model_column=args.model_column,
    )

    # Save results
    os.makedirs(args.output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(
        args.output_dir, f"llm_judge_evaluation_{timestamp}.json"
    )
    evaluator.save_evaluation_results(results, output_path)

    # Generate and print summary
    summary = evaluator.generate_evaluation_summary(results)
    print("\n=== Evaluation Summary ===")
    print(f"Total evaluations: {summary['total_evaluations']}")
    print(f"Models evaluated: {summary['models_evaluated']}")
    print(f"Judge model: {summary['judge_model']}")
    print("\nModel Rankings:")
    for i, stats in enumerate(summary["model_stats"], 1):
        print(
            f"{i}. {stats['model']}: {stats['avg_score']:.2f} ± {stats['std_score']:.2f}"
        )


if __name__ == "__main__":
    asyncio.run(main())
