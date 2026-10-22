"""Program identity audit: algorithm vs constants vs stored examples."""
import ast, hashlib


def audit_program(src: str) -> dict:
    tree = ast.parse(src)
    nums = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool)]
    strs = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    containers = [n for n in ast.walk(tree) if isinstance(n, (ast.List, ast.Tuple, ast.Dict, ast.Set))]
    big = [c for c in containers if sum(isinstance(e, ast.Constant) for e in getattr(c, "elts", getattr(c, "values", []))) >= 3]
    drug_ids = [s for s in strs if s.startswith("#")]
    stmts = sum(isinstance(n, ast.stmt) for n in ast.walk(tree))
    return {"sha256": hashlib.sha256(src.encode()).hexdigest(), "statements": stmts, "numeric_literals": len(nums),
            "distinct_numeric_literals": sorted(set(nums))[:20], "constant_containers_ge3": len(big), "embedded_drug_ids": len(drug_ids),
            "embedded_data_suspected": bool(big or drug_ids)}


def structure_signature(src: str) -> str:
    """Hash of the program with every numeric constant replaced by 0: equal signatures = parameter-only change."""
    class Z(ast.NodeTransformer):
        def visit_Constant(self, n):
            return ast.copy_location(ast.Constant(0), n) if isinstance(n.value, (int, float)) and not isinstance(n.value, bool) else n
    t = Z().visit(ast.parse(src))
    return hashlib.sha256(ast.dump(t).encode()).hexdigest()
