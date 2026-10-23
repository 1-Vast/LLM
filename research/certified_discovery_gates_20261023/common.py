"""Shared paths, constants and helpers for the certified-discovery Gate 0 / Gate 1 study."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "log/20261023/certified_discovery_gates"
DATA = ROOT / "data/processed/certified_discovery_gates_20261023"
AZ_ZIP = ROOT / "data/external/research_sources/20261022/intervention_program_renewal/az_design/matrix_well_stats_GDSC_007_010_plus_Spiper1.zip"
AZ_ZIP_SHA = "e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259"
AZ_MEMBER = "combo_well_stats_GDSC_007_05May22.csv"
AZ_DESIGN = ROOT / "log/20261022/az_paid_reference_gate/DESIGN.json"
JAAKS = ROOT / "data/external/gdsc_combinations/jaaks2022_figshare"
JAAKS_ORIGINAL = JAAKS / "Original screen_All tissues_fitted data.csv"
JAAKS_VALIDATION = JAAKS / "Validation screen_All tissues_fitted data.csv"
JAAKS_RAW = JAAKS / "Original_screen_All_tissues_raw_data.csv.zip"
CERTIFICATION = ROOT / "src/maestro/certification.py"

ALPHA = 0.1
PF_MULTIPLES = np.array([0.25, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0])
CHECK_M = np.linspace(0.05, 10.0, 200)
CHECK_MU = -np.linspace(0.0, 5.0, 101)
GRID = np.linspace(-1.0, 1.0, 401)
N_REPLAYS = 200
N_BOOT = 2000
BOOT_SEED = 20261023
BUDGETS = (1, 2, 3)
GATE1_BUDGETS = (1, 2)
JAAKS_WELLS_PER_READ = 7
INACTIVE_LEVEL = 0.9
MIN_INACTIVE_UNITS = 200


def replay_seed(*parts):
    return int(hashlib.sha256("|".join(["cdg", *map(str, parts)]).encode()).hexdigest()[:16], 16)


def replay_rng(*parts):
    return np.random.default_rng(replay_seed(*parts))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def sha_lf(path):
    """Digest with CRLF normalised to LF, so a checkout under eol=lf does not change it."""
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _plain(obj):
    if isinstance(obj, dict):
        return {str(k): _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return _plain(obj.tolist())
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        v = float(obj)
        return v if np.isfinite(v) else None
    if isinstance(obj, float) and not np.isfinite(obj):
        return None
    return obj


def write_json(path, obj):
    with Path(path).open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(_plain(obj), stream, indent=2)
        stream.write("\n")


def write_text(path, text):
    with Path(path).open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)


def import_certification():
    """Import src/maestro/certification.py by path; the package __init__ pulls in unrelated modules."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("maestro_certification", CERTIFICATION)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TEXT_SUFFIXES = {".py", ".md", ".json", ".txt"}


def digest_matches(path, digest):
    path = Path(path)
    if not path.exists():
        return False
    if path.suffix in TEXT_SUFFIXES:
        return sha_lf(path) == digest["sha256_lf"]
    return sha(path) == digest["sha256"]


def require_freeze():
    """Refuse to run before the freeze, or after a frozen file changed without a DEVIATIONS.md entry naming it."""
    freeze = OUT / "FREEZE.json"
    if not freeze.exists():
        raise SystemExit("FREEZE.json is missing: freeze the protocol before converting responses")
    record = json.loads(freeze.read_text(encoding="utf-8"))
    changed = [name for name, digest in record["files"].items() if not digest_matches(ROOT / name, digest)]
    deviations = OUT / "DEVIATIONS.md"
    logged = deviations.read_text(encoding="utf-8") if deviations.exists() else ""
    unlogged = [name for name in changed if Path(name).name not in logged]
    if unlogged:
        raise SystemExit(f"frozen files changed without a DEVIATIONS.md entry: {unlogged}")
    return record, changed
