CLI Reference
=============

This page documents the command-line interface for the benchmarking harness. Use
these flags to run targeted experiments, validate configurations, and drive CI
workflows.

.. program:: main.py

Common flags
------------

- ``--model <model-key>``
  Run only the model specified in ``models.json`` (e.g., ``gpt-4o-mini``).

- ``--category <name>``
  Run all models with the specified ``category``.

- ``--system_prompt <name>``
  Select the system prompt to use (defaults to ``strict_socratic``).

- ``--include-helm``
  Include HELM-style prompts for robustness and safety testing.

- ``--prompt-range start-end``
  Run a contiguous slice of prompts (e.g., ``1-5``) for smoke tests.

- ``--dry-run``
  Validate configuration and show what would run without issuing live API
  calls.

- ``--template-vars '{"k1": "v1", "k2": 3}'``
  JSON-encoded template variables for Jinja2 prompt expansion. Be careful with
  shell quoting on Windows and Unix shells.

Examples
--------

Run a single model with HELM prompts and template variables:

.. code-block:: bash

   python main.py --model gemini-2.5-flash --prompt-range 1-5 --include-helm \
       --template-vars '{"vehicle_type":"car"}' --system_prompt neutral_instruction

Dry-run a 3-prompt smoke test for adapters:

.. code-block:: bash

   python main.py --prompt-range 1-3 --dry-run

CI-friendly invocation (no secrets, synthetic only):

.. code-block:: bash

   python main.py --dry-run --prompt-range 1-1

Notes
-----

- The CLI is intentionally compact. For programmatic control, import
  ``main.run_benchmark`` and call it from a Python driver.

- When adding new flags, update ``docs/cli.rst`` and the Sphinx docs to keep
  the canonical reference in sync.
