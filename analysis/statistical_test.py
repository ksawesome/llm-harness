import pandas as pd
import numpy as np
from scipy.stats import wilcoxon
from statsmodels.stats.multitest import multipletests
from sklearn.metrics import cohen_kappa_score
from itertools import combinations

# --- Helper Functions ---


def cohen_d(group1, group2):
    """Calculates Cohen's d for independent samples."""
    # Calculate the size of samples
    n1, n2 = len(group1), len(group2)
    # Calculate the variance of the samples
    s1, s2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    # Calculate the pooled standard deviation
    s = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
    # Calculate the means of the samples
    u1, u2 = np.mean(group1), np.mean(group2)
    # Calculate the effect size
    return (u1 - u2) / s


# --- Main Analysis Functions ---


def analyze_inter_rater_reliability(df_human_raw):
    """
    Calculates Cohen's Kappa to measure the agreement between raters.
    This function assumes a 'long' format for the human evaluation data,
    with columns: [response_id, rater_id, pedagogical_quality, contextual_fidelity]
    """
    print("\n--- 1. Inter-Rater Reliability Analysis (Cohen's Kappa) ---")

    required_columns = ["response_id", "rater_id", "pedagogical_quality"]
    missing_columns = [
        col for col in required_columns if col not in df_human_raw.columns
    ]

    if missing_columns:
        print(
            f"Error: Missing required columns for inter-rater reliability: {missing_columns}"
        )
        print(f"Available columns: {list(df_human_raw.columns)}")
        return

    # Pivot the table to get raters' scores side-by-side for each response
    pivot_df = df_human_raw.pivot(
        index="response_id", columns="rater_id", values="pedagogical_quality"
    ).dropna()

    if len(pivot_df.columns) < 2:
        print("Not enough raters to calculate reliability. Need at least 2.")
        return

    rater1_scores = pivot_df.iloc[:, 0]
    rater2_scores = pivot_df.iloc[:, 1]

    kappa = cohen_kappa_score(rater1_scores, rater2_scores)

    print(f"Cohen's Kappa for Pedagogical Quality: {kappa:.4f}")
    if kappa > 0.81:
        print("Result: Almost perfect agreement. The rubric is very reliable.")
    elif kappa > 0.61:
        print("Result: Substantial agreement. The rubric is reliable.")
    elif kappa > 0.41:
        print("Result: Moderate agreement. The rubric is acceptably reliable.")
    else:
        print("Result: Low agreement. Consider rater re-calibration.")


def analyze_model_performance(df_merged):
    """
    Performs pairwise Wilcoxon signed-rank tests to compare model performance.
    Adjusts p-values using the Benjamini-Hochberg procedure.
    """
    print(
        "\n--- 2. Comparative Model Performance Analysis (Wilcoxon Signed-Rank Test) ---"
    )

    required_columns = ["model", "pedagogical_quality"]
    missing_columns = [
        col for col in required_columns if col not in df_merged.columns
    ]

    if missing_columns:
        print(
            f"Error: Missing required columns for model performance analysis: {missing_columns}"
        )
        print(f"Available columns: {list(df_merged.columns)}")
        return

    models = df_merged["model"].unique()
    if len(models) < 2:
        print("Error: Need at least 2 models to perform comparative analysis.")
        return

    model_pairs = list(combinations(models, 2))

    results = []

    # Perform pairwise tests
    for model1, model2 in model_pairs:
        scores1 = df_merged[df_merged["model"] == model1][
            "pedagogical_quality"
        ]
        scores2 = df_merged[df_merged["model"] == model2][
            "pedagogical_quality"
        ]

        if len(scores1) == 0 or len(scores2) == 0:
            print(f"Warning: No data for model pair {model1} vs {model2}")
            continue

        # The prompts are the same for both models, making the samples related
        try:
            stat, p_value = wilcoxon(scores1, scores2)
            results.append(
                {"model1": model1, "model2": model2, "p_value": p_value}
            )
        except ValueError as e:
            print(
                f"Warning: Could not perform Wilcoxon test for {model1} vs {model2}: {e}"
            )
            continue

    if not results:
        print("No valid model pairs to compare.")
        return

    p_values = [res["p_value"] for res in results]

    # Adjust for multiple comparisons
    reject, p_values_adjusted, _, _ = multipletests(
        p_values, alpha=0.05, method="fdr_bh"
    )

    print("\nPairwise Comparison of Pedagogical Quality:")
    for i, res in enumerate(results):
        model1, model2 = res["model1"], res["model2"]
        is_significant = "YES" if reject[i] else "NO"

        # Calculate effect size if significant
        effect_size = "N/A"
        if reject[i]:
            scores1 = df_merged[df_merged["model"] == model1][
                "pedagogical_quality"
            ]
            scores2 = df_merged[df_merged["model"] == model2][
                "pedagogical_quality"
            ]
            d = cohen_d(scores1, scores2)
            effect_size = f"{d:.4f}"

        print(
            f"- {model1:18} vs. {model2:18} | Adjusted p-value: {p_values_adjusted[i]:.4f} | Significant? {is_significant:3} | Cohen's d: {effect_size}"
        )


# --- Main Execution Block ---

if __name__ == "__main__":
    print("Starting LLM Benchmark Statistical Analysis...")

    # --- ACTION REQUIRED: Load your actual data here ---
    # You will need two files:
    # 1. The raw, un-aggregated human scores in a 'long' format.
    # 2. The merged dataframe of harness results and MEAN human scores.
    # Example:
    # human_raw_df = pd.read_csv('../results/raw_output/human_scores_long_format.csv')
    # merged_df = pd.read_csv('../results/processed/merged_results.csv')

    # For now, we'll create placeholder data that mirrors your required
    # structure.
    models_list = [
        "GPT-4o mini",
        "Claude 3 Sonnet",
        "Gemini 1.5 Flash",
        "Command R",
        "Llama 3 8B",
    ]

    # Placeholder for inter-rater reliability
    human_raw_data = {
        "response_id": list(range(50)) * 2,
        "rater_id": ["rater_A"] * 50 + ["rater_B"] * 50,
        "pedagogical_quality": np.random.randint(1, 6, 100),
        "contextual_fidelity": np.random.randint(1, 6, 100),
    }
    human_raw_df = pd.DataFrame(human_raw_data)

    # Placeholder for merged data
    merged_data = {
        "model": np.repeat(models_list, 50),
        "pedagogical_quality": np.random.normal(3, 1, 250),
    }
    merged_df = pd.DataFrame(merged_data)

    # --- Run the Analyses ---
    analyze_inter_rater_reliability(human_raw_df)
    analyze_model_performance(merged_df)

    print("\nAnalysis complete.")
