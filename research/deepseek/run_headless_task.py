"""Run one authorized isolated Harness packet; never retry an uncertain call."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time

root = Path(__file__).resolve().parent
task_dir = (root / "tasks" / sys.argv[1]).resolve()
assert task_dir.parent == (root / "tasks").resolve()
job_path = task_dir / "task.json"
job = json.loads(job_path.read_text(encoding="utf-8-sig"))
assert job["is_execution_authorization"] is True
assert job["transport"] == "isolated_headless_stdin_no_tools"
receipt_path = task_dir / "receipt.json"
if receipt_path.exists():
    raise SystemExit("Receipt exists: no automatic replay.")
packet = (task_dir / "prompt.txt").read_bytes()
assert hashlib.sha256(packet).hexdigest() == job["prompt_sha256"]
assert len(packet) <= job["budget"]["max_stdin_bytes"]
assert job["budget"]["max_output_tokens"] <= 2560
assert job["budget"]["wall_seconds"] <= 180
workspace = (task_dir / "workspace").resolve()
assert workspace.is_dir() and workspace.parent == task_dir
source_profile = Path.home() / ".dsh" / "profiles" / "headless"
runtime = Path(tempfile.mkdtemp(prefix=f"maestro-dsh-{job['task_id']}-", dir=r"D:\CodexData\tmp"))
target_profile = runtime / "profiles" / "headless"
target_profile.mkdir(parents=True)
for name in ("package.json", "cordis.yml", "pnpm-workspace.yaml"):
    raw = (source_profile / name).read_bytes()
    if re.search(rb"sk[-_][A-Za-z0-9_-]{10,}", raw):
        raise SystemExit("Refusing a secret-bearing profile copy.")
    (target_profile / name).write_bytes(raw)
patch_source = Path(r"D:\Rice\GitHub\image-context-understanding-20261028\文档\验证\named-title-context-20261028\harness-profile.yml")
patch = patch_source.read_text(encoding="utf-8-sig")
assert "baseURL: https://api.deepseek.com/anthropic" in patch
assert "model: deepseek-flash" in patch and "thinking: disabled" in patch
patch = re.sub(r"maxTokens: 1800\b", f"maxTokens: {job['budget']['max_output_tokens']}", patch)
(target_profile / "cordis.patch.yml").write_text(patch, encoding="utf-8")
temporary = runtime / "tmp"
temporary.mkdir()
# Use the user's specified existing local credential in memory only.
credential_text = (Path.home() / ".dsh" / ".credentials.yaml").read_text(encoding="utf-8")
match = re.search(r"DEEPSEEK_API_KEY:\s*(\S+)", credential_text)
if not match:
    raise SystemExit("Existing DeepSeek credential was not found; no fallback.")
secret = match.group(1)
del credential_text, match
app = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "DeepSeek Harness"
command = [str(app / "DeepSeek Harness.exe"), "--expose-internals",
           str(app / "resources/app.asar/dsh/node_modules/@deepseek-ai/dsh-desktop-host/lib/cli.js"),
           "--profile", "headless", "--json", "-"]
environment = dict(os.environ, ELECTRON_RUN_AS_NODE="1", DSH_HOME=str(runtime),
                   DSH_PERMISSION_MODE="read-only", DEEPSEEK_API_KEY=secret,
                   TEMP=str(temporary), TMP=str(temporary))
started = time.monotonic()
process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, cwd=workspace, env=environment,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
receipt = {"task_id": job["task_id"], "pid": process.pid, "state": "running",
           "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "job_sha256": hashlib.sha256(job_path.read_bytes()).hexdigest(),
           "prompt_sha256": job["prompt_sha256"], "workspace": str(workspace),
           "dsh_home": str(runtime), "automatic_retry": False,
           "profile_source_sha256": hashlib.sha256(patch_source.read_bytes()).hexdigest(),
           "effective_profile_sha256": hashlib.sha256((target_profile / "cordis.patch.yml").read_bytes()).hexdigest()}
receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
try:
    output, errors = process.communicate(packet, timeout=job["budget"]["wall_seconds"])
    receipt.update(state="exited", exit_code=process.returncode)
except subprocess.TimeoutExpired:
    process.kill()
    output, errors = process.communicate()
    receipt.update(state="timeout_unknown", exit_code=process.returncode)
output = output.replace(secret.encode(), b"<redacted>")
errors = errors.replace(secret.encode(), b"<redacted>")
del secret, environment
(task_dir / "events.jsonl").write_bytes(output)
(task_dir / "stderr.txt").write_bytes(errors)
events = []
for line in output.decode("utf-8", errors="replace").splitlines():
    try:
        events.append(json.loads(line))
    except ValueError:
        pass
final = [e["text"] for e in events if e.get("type") == "final" and isinstance(e.get("text"), str)]
if final:
    (task_dir / "final.md").write_text(final[-1], encoding="utf-8")
usage_events = [e for e in events if "usage" in e or e.get("type") == "usage"]
usage = {"task_id": job["task_id"], "source": "headless --json event stream",
         "stdin_bytes": len(packet), "max_output_tokens": job["budget"]["max_output_tokens"],
         "reported_usage": usage_events or None, "input_tokens": None, "output_tokens": None,
         "paid_cost_usd": None, "missing_reason": None if usage_events else "CLI did not emit token/cost usage",
         "requested_provider": "deepseek-official", "requested_model": "deepseek-flash",
         "effective_model": None, "model_api_requests_confirmed": None,
         "seconds": round(time.monotonic() - started, 3)}
steps = [e["usage"] for e in usage_events if e.get("phase") == "step_end" and isinstance(e.get("usage"), dict)]
if steps:
    usage.update(input_tokens=sum(x.get("inputTokens", 0) for x in steps),
                 output_tokens=sum(x.get("outputTokens", 0) for x in steps),
                 cache_read_tokens=sum(x.get("cacheReadTokens", 0) for x in steps),
                 cache_write_tokens=sum(x.get("cacheWriteTokens", 0) for x in steps),
                 llm_steps=len(steps), aggregate_semantics="sum of distinct step_end events")
(task_dir / "usage.json").write_text(json.dumps(usage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
receipt.update(seconds=usage["seconds"], final_events=len(final),
               session_ids=[e.get("sessionId") for e in events if e.get("type") == "session"],
               events_sha256=hashlib.sha256(output).hexdigest(),
               stderr_sha256=hashlib.sha256(errors).hexdigest())
receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: receipt[k] for k in ("task_id", "state", "exit_code", "seconds", "final_events")}), flush=True)
