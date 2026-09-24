from __future__ import annotations
import argparse, json
from pathlib import Path
from .e0_dir_core import *

def main():
    p=argparse.ArgumentParser(prog="maestro-e0-dir"); sub=p.add_subparsers(dest="command",required=True)
    a=sub.add_parser("audit"); a.add_argument("--out",type=Path,required=True)
    f=sub.add_parser("preflight"); f.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    payload={"schema":"maestro.e0_dir.v1","command":args.command,"status":"not_run","reason":"independent E0 controller scaffold requires frozen case manifest and provider declaration"}
    args.out.parent.mkdir(parents=True,exist_ok=True); args.out.write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8"); print(args.out)
    return 0
if __name__ == "__main__": raise SystemExit(main())


