pv
==

.. rst-class:: lead

   Pretty print and edit ``plan.json`` for AI agent task tracking.

----

**pv** is a lightweight CLI tool that makes viewing and editing ``plan.json`` files
effortless. Designed for AI agent workflows, it provides a clean terminal interface
for tracking tasks, phases, and progress.

.. grid:: 1 1 2 2
   :gutter: 2

   .. grid-item-card:: Getting Started
      :link: guides/quickstart
      :link-type: doc

      Install pv and create your first plan.json in under a minute.

   .. grid-item-card:: CLI Reference
      :link: guides/cli
      :link-type: doc

      Complete reference for all view and edit commands.

   .. grid-item-card:: API Reference
      :link: api/index
      :link-type: doc

      Python API documentation for programmatic usage.

   .. grid-item-card:: Plan Schema
      :link: guides/schema
      :link-type: doc

      Understand the plan.json structure and validation.


Key Features
------------

- **Instant Overview**: See full plan progress with emoji status indicators
- **Smart Navigation**: Jump to current phase, next task, or recently completed
- **Edit In-Place**: Add phases, tasks, mark done - all from the CLI
- **JSON Output**: Machine-readable output for scripting and automation
- **Schema Validation**: Built-in validation against the plan.json spec
- **Automatic Tracking**: Timestamps and progress auto-calculated


Quick Example
-------------

.. code-block:: bash

   # Create a new plan
   pv init "My Project"

   # Add phases and tasks
   pv add-phase "Setup" --desc "Project initialization"
   pv add-task 0 "Create repository" --agent github-git-expert

   # Track progress
   pv start 0.1.1    # Mark in progress
   pv done 0.1.1     # Mark complete

   # View current status
   pv c              # Current phase + next task
   pv                # Full overview


Installation
------------

.. code-block:: bash

   # Install globally with uv
   uv tool install git+https://github.com/JacobCoffee/pv

   # Or install from PyPI
   pip install plan-view


.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Learn

   guides/quickstart
   guides/cli
   guides/schema

.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Reference

   api/index

.. toctree::
   :hidden:
   :caption: Project

   GitHub <https://github.com/JacobCoffee/pv>


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
