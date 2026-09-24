"""Local tools and their shared support code.

Folder layout
- `tools/<tool_id>/` -- a router-discoverable tool: `manifest.json` plus the
  entrypoint it names. `agent.tool_runtime.LocalToolCatalog` discovers exactly the
  directories that carry a manifest, and the controller may select one per turn
  for an explicitly supplied dataset.
- `tools/shared/` -- support code with **no** manifest, so the router never sees
  it. It holds the machinery a caller needs to build a small, registered,
  self-consistent fixture of the kind the framework accepts, and the deterministic
  client stand-ins the tests and offline runners use.

Nothing here is evidence. A tool reports a derived analysis, and a fixture is a
constructed one: neither is a measurement, and neither can discharge a premise.
"""
