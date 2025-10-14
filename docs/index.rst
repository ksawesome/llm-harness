LLM Benchmarking Harness Documentation
=====================================

Welcome to the reference documentation for the LLM Benchmarking Harness. These
pages complement the numbered README guides by describing module APIs, expected
data flows, and extension points in greater technical detail.

### Building the Documentation

.. code-block:: bash

   pip install -e .[dev]
   cd docs
   sphinx-build -b html . _build/html

Open ``_build/html/index.html`` in a browser to browse the generated reference.

### Module Guide

* :mod:`adapters` – provider integrations, retry logic, and synthetic fallback.
* :mod:`analysis` – reporting, comparative analytics, and LLM-as-judge tooling.
* :mod:`utils` – helpers for prompts, result ingestion, and synthetic generation.
* :mod:`web` – Flask endpoints, templating helpers, and REST exports.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   adapters
   analysis
   utils
   web
   cli


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
