# LLM Benchmarking Harness for the Mettle Project

This repository contains the code for the research project, "Selection and Benchmarking of a Large Language Model for Mettle's Socratic and Adaptive Chatbot".

The `llm-harness` is a Python-based tool designed to systematically evaluate and compare various Large Language Models (LLMs) for integration into the Mettle learning platform. The benchmark assesses models on criteria such as pedagogical quality, contextual adaptability, cost, latency, and reliability.

The models under evaluation are:
* OpenAI GPT-4o mini
* Anthropic Claude 3 Sonnet
* Google Gemini 1.5 Flash
* Cohere Command R
* Meta Llama 3 8B Instruct (via Hugging Face)

---

## 🚀 Project Structure

The project is organized into several key directories:

```

llm-harness/
|-- adapters/             \# Modules to connect to each provider's API
|   |-- openai\_adapter.py
|   |-- anthropic\_adapter.py
|   |-- google\_adapter.py
|   |-- cohere\_adapter.py
|   |-- huggingface\_adapter.py
|   |-- **init**.py
|-- analysis/             \# Scripts for data analysis and visualization
|   |-- generate\_visualizations.ipynb
|   |-- statistical\_test.py
|-- data/                 \# Input data for the benchmark
|   |-- test\_prompts.json
|   |-- system\_prompts.json
|-- results/              \# Output directory for raw data and figures
|   |-- raw\_output/
|-- .env                  \# File for storing secret API keys (not version controlled)
|-- .gitignore            \# Specifies files for Git to ignore
|-- main.py               \# The main script to run the entire benchmark
|-- requirements.txt      \# Python dependencies
|-- README.md             \# This file

````

---

## 🔧 Setup Instructions

Follow these steps to set up the project environment.

### 1. Clone the Repository
Clone this repository to your local machine:
```bash
git clone https://github.com/ksawesome/llm-harness
cd llm-harness
````

### 2\. Create a Virtual Environment

It is highly recommended to use a Python virtual environment to manage dependencies.

```bash
# Create the environment
python -m venv venv

# Activate the environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3\. Install Dependencies

Install the required Python libraries from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

*(Note: If `requirements.txt` is not up to date, you can generate it after installing packages with `pip freeze > requirements.txt`)*

### 4\. Configure API Keys

You need to provide your API keys in a `.env` file.

a. Create a file named `.env` in the root of the `llm-harness` directory.
b. Add your keys to the file, following this format:

```env
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
GOOGLE_API_KEY="AIzaSy..."
COHERE_API_KEY="..."
HUGGINGFACE_API_KEY="hf_..."
```

This file is listed in `.gitignore` and will not be committed to the repository.

-----

## ▶️ How to Run the Benchmark

The `main.py` script is the entry point for running the benchmark. You can run the full suite or target specific models and configurations using command-line arguments.

### Run the Full Benchmark

To run the benchmark across all five models using the default "strict\_socratic" system prompt, simply run the script:

```bash
python main.py
```

### Run on a Single Model

Use the `--model` flag to test only one specific model. This is useful for debugging an adapter.

```bash
python main.py --model gemini-1.5-flash-latest
```

### Use a Different System Prompt

Use the `--system_prompt` flag to run the benchmark with one of the alternate system prompts defined in `data/system_prompts.json`. This is for the experiment outlined in Section 8.2 of the paper.

```bash
python main.py --system_prompt hybrid_conversational
```

-----

## 📊 Output and Analysis

### Benchmark Output

The script will generate a single CSV file for each run inside the `results/raw_output/` directory. The filename will be timestamped (e.g., `benchmark_results_20251011_010000.csv`) to prevent overwriting previous results.

### Data Analysis

Once you have collected the data (including the human evaluation scores in a separate CSV), you can use the analysis scripts:

  * **`analysis/statistical_test.py`**: A Python script to run the statistical tests (Cohen's Kappa, Wilcoxon signed-rank) as defined in the research plan.
  * **`analysis/generate_visualizations.ipynb`**: A Jupyter Notebook to process the final data and generate the radar chart, scatterplot, and CDF plot.

<!-- end list -->

```
```