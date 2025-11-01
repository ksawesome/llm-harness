"""
Simulate API calls and scope width analysis for demonstration.
Generates realistic LLM responses and analyzes them for scope width.
"""

import json
import random
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.scope_width_analysis import ScopeWidthAnalyzer

# Simulated responses for different models
NARROW_RESPONSES = [
    "Consider the definition of power.",
    "Think about the units.",
    "What is the relationship between force and velocity?",
    "Power is work per unit time.",
    "Look at your equation again.",
]

APPROPRIATE_RESPONSES = [
    """Good question! Let's think about this step by step. You're using P = F * v, which is correct for instantaneous power. But during acceleration, both force and velocity are changing. Consider: is the velocity constant during the acceleration phase? What would happen if you used the average velocity instead?""",
    """That's a reasonable starting point. Given the mass of 7kg and the friction of 5N, you'll need to calculate the net force required. Remember that F = ma gives you the force needed for acceleration, but you also have to overcome friction. Once you have the total force, think about how velocity changes over time during acceleration.""",
    """I see your approach. Let's break this down: You've identified the key components - force from the motor and the velocity. However, think about whether these values remain constant throughout the motion. During acceleration from rest, how does velocity change? Does the power requirement stay the same throughout, or does it vary?""",
    """Good effort! You're on the right track with considering multiple forces. Let's verify: you mentioned the motor force and friction. Are there any other forces acting on the car? Think about the wheel diameter you were given - why might that be important? It relates to converting between linear motion of the car and rotational motion of the wheels.""",
    """That's an interesting calculation. Let's examine your assumptions: you assumed the car accelerates uniformly, which is a reasonable simplification. Now, for the power estimate, are you looking for the peak power (maximum needed at any instant) or the average power over the acceleration period? These could be quite different values.""",
]

TOO_BROAD_RESPONSES = [
    """That's fascinating! Power calculations have a rich history dating back to James Watt, who invented the term "horsepower" to market his steam engines. By the way, did you know that one horsepower equals 746 Watts? Speaking of units, the Watt itself is named after James Watt. This reminds me of how the SI system revolutionized scientific measurements in the 1960s. As an AI language model, I should mention that I don't have personal experiences, but I can tell you that power is a fundamental concept in physics. Philosophically speaking, the idea of "power" extends beyond physics into social structures and political systems. Now, regarding your equation P = F * v, let's also consider quantum mechanical effects at the atomic level, though those won't matter for your macroscopic calculation.""",
    """Great question! Before we dive in, let me provide some historical context. Electric vehicles actually date back to the 1830s, predating gasoline cars! In fact, Thomas Edison and Henry Ford were close friends who collaborated on electric vehicle development. Speaking of Edison, his rivalry with Nikola Tesla over AC vs DC power is legendary. This brings up an interesting point about power distribution systems. By the way, Tesla's work on alternating current revolutionized the modern world. Now, you might be wondering how this relates to your problem about calculating motor power. Well, the principles of electromagnetism discovered by Faraday and Ampère are fundamental. Also, I should clarify that as an AI, I was trained on a large corpus of text, so my knowledge comes from that training data. Getting back to your question about the car - have you considered what would happen on the moon where gravity is different? Or what about relativistic effects if the car traveled near the speed of light?""",
    """Interesting approach! Power is such a multifaceted concept. In thermodynamics, we deal with heat engines and the Carnot cycle. In electrical engineering, we have reactive power and power factor corrections. In mechanical systems like yours, we're looking at mechanical power. This reminds me - have you taken a course on control theory yet? PID controllers are essential for motor control systems. Speaking of motors, there are many types: DC motors, AC motors, stepper motors, servo motors, brushless motors. Each has different characteristics. By the way, the global market for electric motors is expected to reach $150 billion by 2027. That's quite significant! Now, regarding your calculation, you should also think about the environmental impact of different energy sources. Are you using renewable energy to charge the battery? What's the carbon footprint? These are important questions in modern engineering. Also, did you know that regenerative braking can recover up to 70% of kinetic energy in some systems?""",
]

EDGE_CASE_RESPONSES = [
    """Let me help you focus. The Mettle system is designed for engineering estimation problems, specifically the power calculation for your electric car project. While moon gravity and jellybean estimation are interesting thought experiments, let's stay focused on the task at hand. For your car's power requirement, start by identifying the forces acting on the vehicle and the velocity profile during acceleration.""",
    """I cannot provide direct answers or complete solutions, as that would undermine the learning process. My role is to guide you through Socratic questioning so you can develop your own understanding. Think about what information you've been given and what physical principles apply to this power calculation problem.""",
]

SAFETY_RESPONSES = [
    """I cannot assist with personal, medical, or mental health issues. For stress and anxiety about coursework, I encourage you to reach out to your university's counseling services or student support office. For this engineering problem, I can help guide your technical thinking. Let's focus on the power calculation - what's your first step in approaching this problem?""",
    """I cannot help with academic integrity violations or access secure systems. For questions about your grade or course requirements, please contact your instructor directly. I'm here to help you learn the engineering concepts. Let's work on understanding the power calculation for your project.""",
]


def generate_response(prompt_data: dict, model_name: str) -> str:
    """Generate a simulated response based on prompt category and model."""
    category = prompt_data.get("category", "")
    expected_scope = prompt_data.get("scope_width", "appropriate")

    # Different models have different tendencies
    model_behaviors = {
        "gpt-4": {"narrow": 0.1, "appropriate": 0.7, "broad": 0.2},
        "claude-3-opus": {"narrow": 0.15, "appropriate": 0.75, "broad": 0.1},
        "gemini-pro": {"narrow": 0.2, "appropriate": 0.6, "broad": 0.2},
        "gpt-3.5-turbo": {"narrow": 0.25, "appropriate": 0.55, "broad": 0.2},
    }

    behavior = model_behaviors.get(
        model_name, {"narrow": 0.2, "appropriate": 0.6, "broad": 0.2}
    )

    # Bias toward expected scope but with some variation
    if "Safety" in category or "Edge" in category:
        if "Safety" in category:
            return random.choice(SAFETY_RESPONSES)
        else:
            return random.choice(EDGE_CASE_RESPONSES)

    # Choose response type based on model behavior
    rand = random.random()
    if rand < behavior["narrow"]:
        return random.choice(NARROW_RESPONSES)
    elif rand < behavior["narrow"] + behavior["appropriate"]:
        return random.choice(APPROPRIATE_RESPONSES)
    else:
        return random.choice(TOO_BROAD_RESPONSES)


def simulate_benchmark_run(num_prompts: int = 20, models: list = None):
    """Simulate a benchmark run with multiple models."""

    if models is None:
        models = ["gpt-4", "claude-3-opus", "gemini-pro", "gpt-3.5-turbo"]

    # Load prompts
    with open("data/test_prompts_120.json", encoding="utf-8") as f:
        all_prompts = json.load(f)

    # Select subset of prompts (balanced across categories)
    selected_prompts = random.sample(
        all_prompts, min(num_prompts, len(all_prompts))
    )

    analyzer = ScopeWidthAnalyzer()
    results = []

    print(f"\n{'='*80}")
    print(
        f"SIMULATED BENCHMARK RUN - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    print(f"{'='*80}")
    print(f"Models: {', '.join(models)}")
    print(f"Prompts: {len(selected_prompts)}")
    print(f"{'='*80}\n")

    for prompt_idx, prompt_data in enumerate(selected_prompts, 1):
        print(
            f"Prompt {prompt_idx}/{len(selected_prompts)}: {prompt_data['id']}"
        )

        for model in models:
            # Simulate API call
            response_text = generate_response(prompt_data, model)

            # Simulate latency (ms)
            latency_ms = random.uniform(500, 3000)

            # Simulate token counts
            tokens_in = (
                len(prompt_data["prompt_text"].split()) + 50
            )  # +50 for system prompt
            tokens_out = len(response_text.split())

            # Simulate cost ($/1K tokens, approximate)
            cost_per_1k = {
                "gpt-4": 0.03,
                "claude-3-opus": 0.015,
                "gemini-pro": 0.001,
                "gpt-3.5-turbo": 0.002,
            }
            cost_usd = (
                (tokens_in + tokens_out) / 1000 * cost_per_1k.get(model, 0.01)
            )

            # Analyze scope width
            scope_analysis = analyzer.analyze_scope_width(
                response_text, prompt_data, prompt_data.get("scope_width")
            )

            # Compile result
            result = {
                "timestamp": datetime.now().isoformat(),
                "prompt_id": prompt_data["id"],
                "prompt_category": prompt_data["category"],
                "prompt_text": prompt_data["prompt_text"],
                "prompt_context": prompt_data.get("teacher_context"),
                "expected_scope_width": prompt_data.get("scope_width"),
                "model": model,
                "response_text": response_text,
                "latency_ms": round(latency_ms, 2),
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "cost_usd": round(cost_usd, 6),
                "scope_width_assessed": scope_analysis["assessed_scope"],
                "scope_width_score": scope_analysis["scope_score"],
                "scope_width_confidence": scope_analysis["confidence"],
                "scope_width_matches_expected": scope_analysis[
                    "matches_expected"
                ],
                "scope_width_metrics": scope_analysis["metrics"],
            }

            results.append(result)

            # Print summary
            match_symbol = (
                "✓" if result["scope_width_matches_expected"] else "✗"
            )
            print(
                f"  {model:20s} | Score: {result['scope_width_score']:.1f} | "
                f"Assessed: {result['scope_width_assessed']:12s} | "
                f"Expected: {result['expected_scope_width']:12s} {match_symbol}"
            )

        print()

    return results


def save_results(results: list, output_file: str):
    """Save results to JSON file."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*80}")
    print(f"Results saved to: {output_path}")
    print(f"Total responses: {len(results)}")
    print(f"{'='*80}\n")


def print_summary(results: list):
    """Print summary statistics."""
    from collections import Counter

    print(f"\n{'='*80}")
    print("SUMMARY STATISTICS")
    print(f"{'='*80}\n")

    # Overall accuracy
    total = len(results)
    matches = sum(1 for r in results if r["scope_width_matches_expected"])
    accuracy = matches / total * 100 if total > 0 else 0

    print(f"Overall Accuracy: {accuracy:.1f}% ({matches}/{total})")

    # Per-model accuracy
    print(f"\nPer-Model Accuracy:")
    models = {r["model"] for r in results}
    for model in sorted(models):
        model_results = [r for r in results if r["model"] == model]
        model_matches = sum(
            1 for r in model_results if r["scope_width_matches_expected"]
        )
        model_accuracy = model_matches / len(model_results) * 100
        avg_score = sum(r["scope_width_score"] for r in model_results) / len(
            model_results
        )
        print(
            f"  {model:20s}: {model_accuracy:5.1f}% | Avg Score: {avg_score:.2f}"
        )

    # Scope distribution
    print(f"\nScope Width Distribution (All Models):")
    assessed_scopes = Counter(r["scope_width_assessed"] for r in results)
    for scope, count in assessed_scopes.most_common():
        pct = count / total * 100
        print(f"  {scope:12s}: {count:3d} ({pct:5.1f}%)")

    # Average metrics
    print(f"\nAverage Metrics:")
    avg_latency = sum(r["latency_ms"] for r in results) / total
    avg_tokens_in = sum(r["tokens_in"] for r in results) / total
    avg_tokens_out = sum(r["tokens_out"] for r in results) / total
    avg_cost = sum(r["cost_usd"] for r in results) / total
    avg_confidence = sum(r["scope_width_confidence"] for r in results) / total

    print(f"  Latency: {avg_latency:.0f} ms")
    print(f"  Tokens In: {avg_tokens_in:.0f}")
    print(f"  Tokens Out: {avg_tokens_out:.0f}")
    print(f"  Cost: ${avg_cost:.4f}")
    print(f"  Confidence: {avg_confidence:.2f}")

    print(f"\n{'='*80}\n")


def main():
    """Main execution function."""
    random.seed(42)  # For reproducibility

    # Simulate benchmark with 20 prompts across 4 models = 80 results
    results = simulate_benchmark_run(num_prompts=20)

    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"results/simulated_scope_width_benchmark_{timestamp}.json"
    save_results(results, output_file)

    # Print summary
    print_summary(results)

    # Print example result
    print(f"{'='*80}")
    print("EXAMPLE RESULT (First Entry)")
    print(f"{'='*80}\n")
    example = results[0]
    print(f"Prompt ID: {example['prompt_id']}")
    print(f"Category: {example['prompt_category']}")
    print(f"Model: {example['model']}")
    print(f"\nPrompt Text:")
    print(f"  {example['prompt_text'][:200]}...")
    print(f"\nResponse Text:")
    print(f"  {example['response_text'][:200]}...")
    print(f"\nScope Width Analysis:")
    print(f"  Expected: {example['expected_scope_width']}")
    print(f"  Assessed: {example['scope_width_assessed']}")
    print(f"  Score: {example['scope_width_score']}")
    print(f"  Confidence: {example['scope_width_confidence']}")
    print(f"  Matches: {example['scope_width_matches_expected']}")
    print(f"\nMetrics:")
    for key, value in example["scope_width_metrics"].items():
        print(f"  {key}: {value}")
    print(f"\nPerformance:")
    print(f"  Latency: {example['latency_ms']} ms")
    print(f"  Tokens: {example['tokens_in']} in, {example['tokens_out']} out")
    print(f"  Cost: ${example['cost_usd']}")
    print(f"\n{'='*80}\n")


if __name__ == "__main__":
    main()
