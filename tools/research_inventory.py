"""Read-only research inventory: actual files, pins, imports and duplicate candidates.

No experiments, network access or cleanup run here. Explicit path/hash references
are dependencies; equal bytes or normalized ASTs are only cleanup candidates.
"""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import posixpath
import re
import subprocess


def _git_paths(root: Path, *flags: str) -> set[str]:
    result = subprocess.run(['git', 'ls-files', '-z', *flags, '--', 'research'],
                            cwd=root, capture_output=True, text=True, check=False)
    return set(result.stdout.split('\0')) - {''} if result.returncode == 0 else set()


def build_inventory(root: Path) -> dict:
    """Inspect metadata/static source only, without executing any study entry point."""
    root = root.resolve()
    paths = sorted(p for p in (root / 'research').rglob('*') if p.is_file()
                   and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts
                   and p.name != 'RESEARCH_INVENTORY.json')
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
                normalized = ast.parse(ast.unparse(node)).body[0]
                if isinstance(normalized.body[0], ast.Expr) and isinstance(normalized.body[0].value, ast.Constant):
                    normalized.body = normalized.body[1:]
                fingerprint = hashlib.sha256(ast.dump(normalized, include_attributes=False).encode()).hexdigest()
                functions[fingerprint].append(f'{name}:{node.lineno}:{node.name}')
        records[name].update(imports=sorted(imports), local_import_dependencies=sorted(local))

    modules = defaultdict(list)
    navigation = {'research/REPORT.md', 'research/EVIDENCE.md', 'research/INDEX.md',
                  'research/SCIENTIFIC_STATUS.json', 'research/REFACTOR_REPORT.md', 'research/LANGUAGE_AUDIT.json'}
    for name, record in records.items():
        parts = Path(name).parts
        module = '/'.join(parts[:3]) if len(parts) > 3 and parts[1] in ('astra', 'decision_value') else '/'.join(parts[:2]) if len(parts) > 2 else 'research'
        category = 'E' if name in navigation else 'C' if name.endswith('P06_READINESS.md') else 'D'
        record.update(module=module, category=category, referenced_by=sorted(pins[name]),
                      cleanup='Generated reading view' if category == 'E' else 'Retain original bytes; no deletion authorized by this inventory')
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
    return dict(schema_version=1, scope='Current selected worktree research files; cache/bytecode excluded; inventory file excluded to avoid self-reference',
                categories=dict(A='Mature core candidate', B='Mature tool', C='Active design', D='Frozen/historical evidence conservatively retained', E='Generated navigation', F='Missing external asset; BLOCKED_ASSETS.md'),
                totals=dict(files=len(records), bytes=sum(r['bytes'] for r in records.values()), modules=len(summaries), python_files=len(python_trees)),
                modules=summaries, files=list(records.values()),
                byte_identical_groups=[dict(sha256=digest, paths=names, automatically_removable=False) for digest, names in sorted(byte_groups.items()) if len(names) > 1],
                duplicate_AST_candidates=[dict(fingerprint=digest, locations=names, equivalent_scientific_semantics_proven=False) for digest, names in sorted(functions.items()) if len(names) > 1],
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
