# Configuration file for the Sphinx documentation builder.

import os
import sys

sys.path.insert(0, os.path.abspath(".."))

# -- Project information -----------------------------------------------------
project = "LLM Benchmarking Harness"
copyright = "2025, ksawesome"
author = "ksawesome"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
html_theme = "alabaster"
html_static_path = ["_static"]

# -- Autodoc settings -------------------------------------------------------
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

# -- Napoleon settings ------------------------------------------------------
napoleon_google_docstring = True
napoleon_numpy_docstring = True

# -- Autodoc mock imports -------------------------------------------------
autodoc_mock_imports = [
    "cohere",
    "google",
    "google.generativeai",
    "tiktoken",
    "requests",
    "openai",
    "anthropic",
    "transformers",
    "huggingface_hub",
    "plotly",
    "matplotlib",
    "reportlab",
]
