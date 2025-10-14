Adapters
========

This module contains API adapters for different LLM providers.

Each adapter delegates to the corresponding provider SDK when keys are
available and gracefully falls back to :mod:`utils.mock_provider` for
synthetic data generation during tests or offline analysis.

Usage Notes
-----------

* All adapter functions return dictionaries matching the schema used in
   ``main.py`` and the report generators. Ensure custom adapters include the
   keys ``model_version``, ``latency_ms``, ``tokens_in``, ``tokens_out``,
   ``cost_usd``, ``response_text``, and ``error_message``.
* When an adapter raises an exception, the orchestrator triggers the synthetic
   fallback. Keep errors descriptive to simplify postmortem analysis.
* Adapters should remain side-effect free and stateless; rate limiting is
   enforced by the harness.

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
