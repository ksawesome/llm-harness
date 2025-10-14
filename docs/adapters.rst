Adapters
========

This module contains API adapters for different LLM providers.

Each adapter delegates to the corresponding provider SDK when keys are
available and gracefully falls back to :mod:`utils.mock_provider` for
synthetic data generation during tests or offline analysis.

.. automodule:: adapters
   :members:
   :undoc-members:
   :show-inheritance:

OpenAI Adapter
--------------

.. automodule:: adapters.openai_adapter
   :members:
   :undoc-members:
   :show-inheritance:

Anthropic Adapter
-----------------

.. automodule:: adapters.anthropic_adapter
   :members:
   :undoc-members:
   :show-inheritance:

Google Adapter
--------------

.. automodule:: adapters.google_adapter
   :members:
   :undoc-members:
   :show-inheritance:

Cohere Adapter
--------------

.. automodule:: adapters.cohere_adapter
   :members:
   :undoc-members:
   :show-inheritance:

Hugging Face Adapter
--------------------

.. automodule:: adapters.huggingface_adapter
   :members:
   :undoc-members:
   :show-inheritance:
