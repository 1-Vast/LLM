"""Per-discovery reuse must retain exact source identity and execution refusal."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from agent.tool_runtime import LocalToolCatalog, ToolRouter, ToolRuntimeError


ROOT = Path(__file__).resolve().parents[1]


def custom_tool(tmp_path):
    root = tmp_path / "tools"
    directory = root / "custom"
    directory.mkdir(parents=True)
    manifest = {"id": "custom", "name": "Fixture", "description": "Source identity fixture.",
                "entrypoint": "tool.py", "required_parameters": ["dataset_path"],
                "evidence_kind": "derived_analysis", "source_files": ["dependency.py"]}
    (directory / "manifest.json").write_text(json.dumps(manifest))
    (directory / "tool.py").write_text("def run(parameters): return {'schema_version': '1.0', 'payload': {}}\n")
    return root


def test_shared_sources_read_once_and_versions_equal_independent_descriptors():
    catalog = LocalToolCatalog(ROOT / "tools")
    original = Path.read_bytes
    reads = {}

    def read(path):
        reads[path] = reads.get(path, 0) + 1
        return original(path)

    with patch.object(Path, "read_bytes", read):
        descriptors = catalog.discover()
    sources = {path for item in descriptors for path in item.source_files}
    assert sources and all(reads[path] == 1 for path in sources)
    for item in descriptors:
        independent = catalog._descriptor(item.manifest_path)
        assert item == independent


def test_same_size_same_timestamp_source_change_invalidates(tmp_path):
    import os
    source = tmp_path / "dependency.py"
    source.write_text("VALUE = 1\n")
    root = custom_tool(tmp_path)
    catalog = LocalToolCatalog(root)
    first = catalog.discover()[0]
    stat = source.stat()
    source.write_text("VALUE = 2\n")
    os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    second = catalog.discover()[0]
    assert first.tool_version_sha256 != second.tool_version_sha256
    with pytest.raises(ToolRuntimeError, match="version changed"):
        ToolRouter._invoke(first, {"dataset_path": "unused"})


def test_dependency_removed_or_replaced_after_discovery_refuses(tmp_path):
    source = tmp_path / "dependency.py"
    source.write_text("VALUE = 1\n")
    root = custom_tool(tmp_path)
    catalog = LocalToolCatalog(root)
    catalog.discover()
    source.unlink()
    with pytest.raises(ToolRuntimeError, match="Invalid tool manifest"):
        catalog.discover()


def test_concurrent_discovery_uses_separate_scopes():
    catalog = LocalToolCatalog(ROOT / "tools")
    expected = catalog.discover()
    with ThreadPoolExecutor(max_workers=4) as workers:
        results = list(workers.map(lambda _: catalog.discover(), range(8)))
    assert all(result == expected for result in results)
