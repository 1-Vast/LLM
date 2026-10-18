"""Launcher: runs a stage with this study's `seal` module (the predecessor study has a module of the same name).

File summary
- Path: research/acquisition_program_20261018/launch.py
- Purpose: `ap_task` puts the predecessor study on sys.path (for bench, loop, rules, metrics); its `seal.py` would shadow this
  study's. The launcher registers this study's seal first, so the frozen files are used unchanged.
- Usage: ``python -B launch.py build-held | evaluate``
"""
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("seal", HERE / "seal.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sys.modules["seal"] = mod
sys.path.insert(0, str(HERE))

if __name__ == "__main__":
    if sys.argv[1] == "build-held":
        import ap_build
        ap_build.main("held")
    elif sys.argv[1] == "evaluate":
        import evaluate
        evaluate.main()
