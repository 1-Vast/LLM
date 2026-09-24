"""Run ``python -m agent`` as a command-line entry point.

File summary
- Path: src/agent/__main__.py
- Purpose: Launch the MAESTRO CLI when the package is executed as a module.
- Core points:
  - Delegates to `cli.main` and propagates its process exit code.
- Interfaces: (module entry point)
- Depends on: agent.cli
"""

from .cli import main

raise SystemExit(main())
