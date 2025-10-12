"""
This file makes the 'adapters' directory a Python package.

It imports the main function from each adapter module so that they can be
easily accessed from other parts of the application, such as main.py.

This allows for cleaner imports, e.g., 'from adapters import call_openai_api'
instead of 'from adapters.openai_adapter import call_openai_api'.
"""

from .openai_adapter import call_openai_api
from .anthropic_adapter import call_anthropic_api
from .google_adapter import call_google_api
from .cohere_adapter import call_cohere_api
from .huggingface_adapter import call_huggingface_api

# The __all__ list defines the public API for this package.
# When a user performs 'from adapters import *', only these names
# will be imported.
__all__ = [
    "call_openai_api",
    "call_anthropic_api",
    "call_google_api",
    "call_cohere_api",
    "call_huggingface_api",
]
