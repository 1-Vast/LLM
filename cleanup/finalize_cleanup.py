from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "cleanup/CLEANUP_MANIFEST.json"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    removed = []
    missing = []
    for row in manifest["planned_deletions"]:
        path = ROOT / Path(row["path"])
        row["status"] = "REMOVED" if not path.exists() else "ALREADY_MISSING"
        (removed if not path.exists() else missing).append(row)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    tracked = [row for row in removed if row["commit_blob"]]
    local = [row for row in removed if row["commit_blob"] is None]
    python_lines = 0
    for row in tracked:
        if not row["path"].endswith(".py"):
            continue
        content = subprocess.run(
            ["git", "show", f"540bc85801fa78a3a58780b37b81b4197449d107:{row['path']}"],
            cwd=ROOT, check=True, capture_output=True,
        ).stdout
        python_lines += len(content.splitlines())

    tracked_status = subprocess.run(
        ["git", "ls-files", "-d", "-z"], cwd=ROOT, check=True,
        capture_output=True, text=True,
    ).stdout.split("\0")
    tracked_bytes = sum(row["size_bytes"] for row in tracked)
    local_bytes = sum(row["size_bytes"] for row in local)
    stats = {
        "baseline_commit": "540bc85801fa78a3a58780b37b81b4197449d107",
        "branch": "cleanup/max-compress-20261009",
        "post_tracked_file_count": 5493 - len(tracked),
        "post_tracked_bytes": 1101507763 - tracked_bytes,
        "removed_tracked_file_count": len(tracked),
        "removed_tracked_bytes": tracked_bytes,
        "removed_local_output_file_count": len(local),
        "removed_local_output_bytes": local_bytes,
        "removed_total_file_count": len(removed),
        "removed_total_bytes": tracked_bytes + local_bytes,
        "removed_python_lines": python_lines,
        "already_missing_file_count": len(missing),
        "remaining_tracked_deletions": len([name for name in tracked_status if name]),
        "history_rewrite_performed": False,
    }
    (ROOT / "cleanup/POST_CLEANUP_STATS.json").write_text(
        json.dumps(stats, indent=2) + "\n", encoding="utf-8"
    )
    lines = [f"{row['status']}\t{row['path']}\t{row['size_bytes']}" for row in manifest["planned_deletions"]]
    (ROOT / "cleanup/REMOVED_PATHS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
