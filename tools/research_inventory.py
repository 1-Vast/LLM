"""Read-only research inventory: actual files, pins, imports and duplicate candidates.

No experiments, network access or cleanup run here. Explicit path/hash references
are dependencies; equal bytes or normalized ASTs are only cleanup candidates.
"""
from __future__ import annotations

import argparse
import ast
import copy
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import posixpath
import re
import subprocess


def _function_fingerprint(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    normalized = copy.deepcopy(node)
    if normalized.body and isinstance(normalized.body[0], ast.Expr) and isinstance(normalized.body[0].value, ast.Constant):
        if isinstance(normalized.body[0].value.value, str):
            normalized.body = normalized.body[1:]
    return hashlib.sha256(ast.dump(normalized, include_attributes=False).encode()).hexdigest()


def _git_paths(root: Path, *flags: str, scope: str = 'research') -> set[str]:
    result = subprocess.run(['git', 'ls-files', '-z', *flags, '--', scope],
                            cwd=root, capture_output=True, text=True, check=False)
    return set(result.stdout.split('\0')) - {''} if result.returncode == 0 else set()


def _repository_inventory(root: Path) -> dict:
    """Collect repository structure and static references without importing project code."""
    excluded = {'.git'}
    paths = sorted(path for path in root.rglob('*') if path.is_file()
                   and not excluded.intersection(path.relative_to(root).parts)
                   and path.name != 'REFACTOR_INVENTORY.json')
    tracked = _git_paths(root, scope='.')
    ignored = _git_paths(root, '--others', '--ignored', '--exclude-standard', scope='.')
    records = []
    top_level = defaultdict(lambda: {'files': 0, 'bytes': 0})
    large_files = []
    relevant = {'src', 'tools', 'tests', 'research', 'log', 'cleanup'}
    counts = defaultdict(lambda: {'files': 0, 'python_files': 0, 'bytes': 0})
    import_edges = defaultdict(set)
    duplicate_functions = defaultdict(list)
    module_entry_points = []
    report_links, test_references = [], []
    python_paths = [path for path in paths if path.suffix == '.py'
                    and path.relative_to(root).parts[0] in {'src', 'tools', 'research'}]
    modules = {}
    for path in python_paths:
        relative = path.relative_to(root).as_posix()
        modules[relative[:-3].replace('/', '.').removesuffix('.__init__')] = relative
    for path in paths:
        relative = path.relative_to(root).as_posix()
        size = path.stat().st_size
        state = 'tracked' if relative in tracked else 'ignored' if relative in ignored else 'untracked'
        cache = bool(re.search(r'(^|/)(?:\.pytest_cache|__pycache__)(?:/|$)|\.py[co]$', relative, re.I))
        if cache:
            decision, reason = 'DELETE', 'Regenerable Python or pytest cache; no source or evidence depends on these bytes.'
        elif relative.startswith(('src/', 'tools/', 'tests/')):
            decision, reason = 'KEEP', 'Production API, reusable tool, or behavioral contract; no dead-code proof established.'
        elif relative.startswith('research/'):
            decision, reason = 'KEEP', 'Research protocol, result, failure, receipt, or source material retained pending semantic review.'
        elif relative.startswith('log/'):
            decision, reason = 'KEEP', 'Dated verification receipt or canonical audit record.'
        elif relative.startswith(('build/', 'maestro.egg-info/')):
            decision, reason = 'DELETE', 'Regenerable package build or installation metadata; removal command was rejected by the local execution policy.'
        elif relative.startswith(('data/', 'reference/', 'outputs/', 'tmp/', '.build-1009/', 'output-1009/')):
            decision, reason = 'BLOCKED', 'Asset/output semantics or external receipt dependencies need owner-level validation.'
        else:
            decision, reason = 'KEEP', 'Tracked project file with no verified deletion basis.'
        records.append({'path': relative, 'bytes': size, 'git_state': state,
                        'decision': decision, 'decision_reason': reason})
        parent = path.relative_to(root).parts[0]
        top_level[parent]['files'] += 1
        top_level[parent]['bytes'] += size
        if parent in relevant:
            counts[parent]['files'] += 1
            counts[parent]['python_files'] += path.suffix == '.py'
            counts[parent]['bytes'] += size
        if size >= 10 * 1024 * 1024:
            large_files.append({'path': relative, 'bytes': size})
        if path.suffix == '.py' and parent in {'src', 'tools', 'research'}:
            try:
                tree = ast.parse(path.read_text(encoding='utf-8-sig'), filename=relative)
            except (SyntaxError, UnicodeError):
                continue
            module = relative[:-len('/__main__.py')].replace('/', '.') if relative.endswith('/__main__.py') else None
            is_main = any(isinstance(node, ast.If) and '__name__' in ast.unparse(node.test)
                          and '__main__' in ast.unparse(node.test) for node in tree.body)
            if module:
                module_entry_points.append({'module': module, 'kind': 'python -m'})
            elif is_main:
                module_entry_points.append({'module': relative[:-3].replace('/', '.'), 'kind': 'python -m'})
            owner = 'research' if parent == 'research' else 'formal'
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and len(node.body) > 2:
                    fingerprint = _function_fingerprint(node)
                    duplicate_functions[fingerprint].append(f'{relative}:{node.lineno}:{node.name}')
                name = node.module if isinstance(node, ast.ImportFrom) else None
                if isinstance(node, ast.Import):
                    imported = [item.name for item in node.names]
                elif isinstance(node, ast.ImportFrom):
                    imported = [name or '']
                else:
                    continue
                for module in imported:
                    if module == 'research' or module.startswith('research.'):
                        import_edges[f'{owner}_imports_research'].add(relative)
                    if parent == 'research' and (module == 'agent' or module.startswith(('agent.', 'maestro.', 'virtual_cell.'))):
                        import_edges['research_imports_formal'].add(relative)
        if path.suffix.lower() in {'.md', '.rst'}:
            try:
                body = path.read_text(encoding='utf-8')
            except UnicodeError:
                continue
            if parent == 'research':
                for match in re.finditer(r'\[[^\]]+\]\(([^)]+\.md(?:#[^)]+)?)\)', body):
                    target = match.group(1)
                    target_path = target.split('#', 1)[0]
                    destination = (path.parent / target_path).resolve() if target_path else path
                    external = bool(re.match(r'^(?:https?|mailto):', target, re.I))
                    report_links.append({
                        'source': relative,
                        'target': target,
                        'resolution': 'EXTERNAL' if external else 'RESOLVED' if destination.is_file() else 'BLOCKED',
                        'reason': 'External URL; not checked as a local file.' if external else None if destination.is_file() else 'Referenced file is absent from this checkout or retained third-party source bundle.',
                    })
        if parent == 'tests' and path.suffix == '.py':
            try:
                body = path.read_text(encoding='utf-8')
            except UnicodeError:
                continue
            for match in re.finditer(r'["\']((?:research|log|output[^/\\]*)[/\\][^"\']+)["\']', body):
                test_references.append({'source': relative, 'target': match.group(1)})

    project = {}
    config = root / 'pyproject.toml'
    if config.is_file():
        try:
            import tomllib
            project = tomllib.loads(config.read_text(encoding='utf-8'))
        except (ImportError, ValueError, UnicodeError):
            pass
    entry_points = [{'command': name, 'target': target}
                    for name, target in project.get('project', {}).get('scripts', {}).items()]
    entry_points.extend(module_entry_points)
    generated = [record['path'] for record in records
                 if re.search(r'(^|/)(?:\.pytest_cache|__pycache__|build|\.build[^/]*|outputs?|tmp)(?:/|$)|\.py[co]$', record['path'], re.I)]
    return {
        'root_directory_count': sum(path.is_dir() for path in root.iterdir() if path.name != '.git'),
        'top_level_directory_counts': dict(sorted(top_level.items())),
        'scoped_counts': dict(sorted(counts.items())),
        'file_count': len(records),
        'python_file_count': sum(path.suffix == '.py' for path in paths),
        'total_bytes': sum(item['bytes'] for item in records),
        'files': records,
        'large_files_10mb_or_more': sorted(large_files, key=lambda item: -item['bytes']),
        'imports': {key: sorted(value) for key, value in sorted(import_edges.items())},
        'cli_entry_points': entry_points,
        'duplicate_function_candidates': [
            {'fingerprint': fingerprint, 'locations': locations, 'semantics_reviewed': False}
            for fingerprint, locations in sorted(duplicate_functions.items()) if len(locations) > 1
        ],
        'test_references': test_references,
        'research_markdown_links': report_links,
        'unresolved_research_markdown_links': [
            item for item in report_links if item['resolution'] == 'BLOCKED'
        ],
        'external_research_markdown_links': [
            item for item in report_links if item['resolution'] == 'EXTERNAL'
        ],
        'generated_or_cache_candidates': generated,
        'decision_totals': {status: sum(item['decision'] == status for item in records)
                            for status in ('KEEP', 'MERGE', 'PROMOTE', 'DELETE', 'BLOCKED')},
        'completed_refactor_actions': [
            {'path': 'Innovation.md', 'decision': 'DELETE', 'reason': 'Removed duplicate proposal note after checking runtime, test, CLI, report and receipt references; historical test receipts remain.'},
            {'path': 'research/targeted_review_20261011.md', 'decision': 'DELETE', 'reason': 'Unreferenced exploratory review with no protocol, test or receipt; its next-step recommendations were superseded.'},
            {'path': 'research/RESEARCH_INVENTORY.json', 'decision': 'DELETE', 'reason': 'Replaced the duplicate 3 MB generated inventory with the requested sole repository inventory; inbound navigation and command references were updated.'},
            {'path': 'README.md', 'decision': 'MERGE', 'reason': 'Consolidated product boundary and navigation; detailed scientific conclusions live in research/REPORT.md and EVIDENCE.md.'},
            {'path': 'research/REPORT.md', 'decision': 'MERGE', 'reason': 'Consolidated current conclusions; detailed cross-study numbers remain in research/EVIDENCE.md.'},
        ],
        'deferred_cleanup': [
            {'path': '.pytest_cache/, __pycache__/, build/, maestro.egg-info/', 'decision': 'BLOCKED', 'reason': 'The execution policy rejected the authorized recursive cache/build removal command; paths remain ignored/regenerable and are listed for a later cleanup.'}
        ],
        'existing_promotions_verified': [
            {'path': 'src/virtual_cell/transcriptional_transfer.py', 'status': 'KEEP', 'reason': 'Existing scoped promotion has regression tests and no research import dependency; not newly promoted in this refactor.'}
        ],
        'limitations': ['Textual references and AST imports are static; dynamic path construction may not be detected.',
                        'Generated/cache candidates are not deletion approvals.'],
    }


def build_inventory(root: Path) -> dict:
    """Inspect metadata/static source only, without executing any study entry point."""
    root = root.resolve()
    paths = sorted(p for p in (root / 'research').rglob('*') if p.is_file()
                   and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts
                   and p.name not in {'RESEARCH_INVENTORY.json', 'REFACTOR_INVENTORY.json'})
    tracked = _git_paths(root)
    ignored = _git_paths(root, '--others', '--ignored', '--exclude-standard')
    records, pins, byte_groups, functions = {}, defaultdict(set), defaultdict(list), defaultdict(list)
    module_paths = {}
    python_trees = {}
    json_documents = {}
    for path in paths:
        name = path.relative_to(root).as_posix()
        body = path.read_bytes()
        digest = hashlib.sha256(body).hexdigest()
        records[name] = dict(path=name, bytes=len(body), sha256=digest,
                             git_state='tracked' if name in tracked else 'ignored' if name in ignored else 'untracked')
        byte_groups[digest].append(name)
        if path.suffix == '.json':
            try:
                json_documents[name] = json.loads(body)
            except (ValueError, UnicodeError):
                records[name]['parse_status'] = 'INVALID_JSON'
        if path.suffix == '.py':
            module = name[:-3].replace('/', '.').removesuffix('.__init__')
            module_paths[module] = name
            try:
                tree = ast.parse(body.decode('utf-8-sig'), filename=name)
                python_trees[name] = tree
            except (SyntaxError, UnicodeError) as error:
                records[name]['parse_status'] = type(error).__name__

    def reference(path, owner):
        path = path.replace('\\', '/')
        for candidate in (posixpath.normpath(path), posixpath.normpath(Path(owner).parent.as_posix() + '/' + path)):
            if candidate in records:
                pins[candidate].add(owner)

    def visit(value, owner):
        if isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, str) and re.fullmatch('[0-9a-fA-F]{64}', item) and isinstance(key, str):
                    reference(key, owner)
                visit(item, owner)
            if isinstance(value.get('path'), str) and isinstance(value.get('sha256'), str):
                reference(value['path'], owner)
        elif isinstance(value, list):
            for item in value:
                visit(item, owner)

    for owner, value in json_documents.items():
        visit(value, owner)
    for name, tree in python_trees.items():
        imports, local = set(), set()
        parent = name[:-3].replace('/', '.').split('.')[:-1]
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.Import):
                modules = [item.name for item in node.names]
            elif isinstance(node, ast.ImportFrom):
                prefix = parent[:len(parent) - node.level + 1] if node.level else []
                base = '.'.join(prefix + ([node.module] if node.module else []))
                modules = [base] + [base + '.' + item.name for item in node.names]
            for module in modules:
                imports.add(module)
                if module in module_paths:
                    local.add(module_paths[module])
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and len(node.body) > 2:
                fingerprint = _function_fingerprint(node)
                functions[fingerprint].append(f'{name}:{node.lineno}:{node.name}')
        records[name].update(imports=sorted(imports), local_import_dependencies=sorted(local))

    modules = defaultdict(list)
    navigation = {'research/REPORT.md', 'research/EVIDENCE.md', 'research/INDEX.md',
                  'research/SCIENTIFIC_STATUS.json', 'research/REFACTOR_INVENTORY.json'}
    for name, record in records.items():
        parts = Path(name).parts
        module = '/'.join(parts[:3]) if len(parts) > 3 and parts[1] in ('astra', 'decision_value') else '/'.join(parts[:2]) if len(parts) > 2 else 'research'
        category = 'E' if name in navigation else 'C' if name.endswith('P06_READINESS.md') else 'D'
        module_names = [item['path'] for item in modules[module]]
        has_readme = any(Path(path).name == 'README.md' for path in module_names)
        has_frozen_or_test_record = any(
            'protocol' in Path(path).name.lower()
            or 'freeze' in Path(path).name.lower()
            or 'receipt' in Path(path).name.lower()
            or Path(path).name.startswith('test_')
            for path in module_names
        )
        if category == 'E' or (has_readme and has_frozen_or_test_record):
            decision = 'KEEP'
            reason = 'Canonical report/index or documented study with a protocol, freeze, receipt, or test.'
        else:
            decision = 'BLOCKED'
            reason = 'No complete study ownership/reproduction record was established by static inventory; semantic review required.'
        record.update(module=module, category=category, referenced_by=sorted(pins[name]),
                      decision=decision, decision_reason=reason,
                      cleanup='Generated reading view' if category == 'E' else 'No automatic deletion authorized')
        modules[module].append(record)
    summaries = []
    for name, items in sorted(modules.items()):
        filenames = [r['path'] for r in items]
        summaries.append(dict(module=name, files=len(items), bytes=sum(r['bytes'] for r in items),
                              category='C' if any(r['category'] == 'C' for r in items) else 'E' if name == 'research' else 'D',
                              entry_points=[p for p in filenames if Path(p).name in ('README.md', 'run.py', 'validation.py', 'verify.py') or Path(p).name.startswith('verify') and p.endswith('.py')],
                              freezes=[p for p in filenames if 'freeze' in Path(p).name.lower() and p.endswith('.json')],
                              protocols=[p for p in filenames if 'protocol' in Path(p).name.lower()],
                              reproduction_status='See SCIENTIFIC_STATUS.json and canonical receipts; inventory does not execute experiments',
                              promotion_status='Frozen algorithms remain research; pure axis/variance arithmetic promoted separately',
                              next_action='Use INDEX.md; preserve path/hash dependencies'))
    return dict(schema_version=2, scope='Repository structure and selected worktree research evidence; the inventory file is excluded to avoid self-reference',
                refactor_baseline=dict(source='Initial read-only inventory before edits', root_directories=18,
                                       tracked_files=13967,
                                       research_files=13405,
                                       research_bytes=580183721,
                                       note='The baseline research scope excludes Python/pytest caches and RESEARCH_INVENTORY.json; repository-wide ignored data bytes were not measured in that pass.'),
                categories=dict(A='Mature core candidate', B='Mature tool', C='Active design', D='Frozen/historical evidence conservatively retained', E='Generated navigation', F='Missing external asset; BLOCKED_ASSETS.md'),
                totals=dict(files=len(records), bytes=sum(r['bytes'] for r in records.values()), modules=len(summaries), python_files=len(python_trees)),
                modules=summaries, files=list(records.values()),
                byte_identical_groups=[dict(sha256=digest, paths=names, automatically_removable=False) for digest, names in sorted(byte_groups.items()) if len(names) > 1],
                duplicate_AST_candidates=[dict(fingerprint=digest, locations=names, equivalent_scientific_semantics_proven=False) for digest, names in sorted(functions.items()) if len(names) > 1],
                repository=_repository_inventory(root),
                limitations=['Explicit JSON path/hash pins and static Python imports only; dynamic dependencies may be absent.',
                             'Equal bytes/functions do not establish safe deletion across frozen protocols.',
                             'No scientific output, independence or benefit is inferred from file names or this inventory.'])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = build_inventory(args.workspace)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result['totals']))


if __name__ == '__main__':
    main()
