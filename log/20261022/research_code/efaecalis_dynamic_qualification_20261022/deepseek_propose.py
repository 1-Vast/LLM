"""One retained proposal request; never reveal settings or execute generated code."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT = ROOT / "log/20261022/efaecalis_dynamic_qualification"
receipt_path = OUT / "DEEPSEEK_RECEIPT.json"
if receipt_path.exists() or (OUT / "DEEPSEEK_PROMPT.md").exists():
    raise FileExistsError("Proposal request already started")
source = ROOT / "log/20261022/dynamic_source_followup/ncbi_scout/REPORT.md"
history = ROOT / "research/REPORT.md"
instructions = """请作为严谨但有创造力的科研机制提案者，提出最多两个极简、可证伪的候选。
目标是虚拟细胞世界模型驱动的药物发现research agent，并使改进策略本身在继承后更会改进。
不要把评估设计当算法，也不要给新名字重复已有操作。你没有检索工具；所有额外文献主张必须标待一手核验，不能编造引用。

已停构造：time-warp普通系统辨识；history predicate split与普通MDLsplit相同；Gaussian gene residual writeback严格等价同信息kernel conditioning；显式haplotype mutation-selection是普通模型且边际频率不足haplotype。Hyperagents/AIDE²/SpecRSI/MetaShare已有任务与meta程序编辑、失败检索和后继改进credit。当前E.faecalis来源原文已做time-varying collateral-profile MDP和backward planning。

已知模块也可以构成真正新贡献，但你必须指出一个具体的新约束、推断/更新操作、识别条件或计算/样本性质，而不能要求通用direct模型无法表示它。给定目前真实数据，可提出条件性假设，不能假装未公开数据已存在。
最多两候选，每候选回答：(1)具体药物实验/功能应用；(2)10行内的最小操作/公式；(3)与最接近普通方法的实质差异及可能精确归约；(4)真正需要的状态/功能/反馈数据和未认证缺口；(5)能最快杀死它的实验；(6)world、agent、权重/程序继承、联合和improver m1胜m0的不同可证伪预测。强same-information direct、ordinaryrefit/continual、AL、simplemixture、equalbudgetsearch必须公平。若只能剩普通应用，明确none并说明原因；不要为了none而省略严肃尝试。输出不超过2500中文字符。
"""
context = "\n\n项目近期决策（节选）：\n" + history.read_text(encoding="utf-8")[:12000]
context += "\n\n新一手来源报告：\n" + source.read_text(encoding="utf-8")
prompt = instructions + context
(OUT / "DEEPSEEK_PROMPT.md").write_text(prompt, encoding="utf-8")
client = DeepSeekChatClient(MAESTROSettings.from_workspace(ROOT))
receipt = {"started_utc": datetime.now(timezone.utc).isoformat(),
           "logical_completion_requests": 1, "transport_attempt_count": "NOT_EXPOSED_BY_CLIENT",
           "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
           "input_files": {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (source, history)},
           "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           "biological_experiment": False}
try:
    response = client.complete([{"role": "system", "content": "你是科研方法提案者，保持具体，区分假设和证据。"},
                                {"role": "user", "content": prompt}],
                               temperature=0.7, max_tokens=6000, thinking_enabled=False)
    (OUT / "DEEPSEEK_PROPOSAL.md").write_text(response.content, encoding="utf-8")
    receipt.update({"status": "RESPONSE_RETAINED", "model": response.model,
                    "finish_reason": response.finish_reason, "content_characters": len(response.content)})
except Exception as error:
    receipt.update({"status": "FAILED_RETAINED", "error_type": type(error).__name__,
                    "error_code": getattr(error, "code", None)})
finally:
    receipt.update({"ended_utc": datetime.now(timezone.utc).isoformat(), "provider_usage": client.provider_usage})
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
print(json.dumps({k: receipt.get(k) for k in ("status", "finish_reason", "provider_usage", "error_type")}))
raise SystemExit(0 if receipt["status"] == "RESPONSE_RETAINED" else 1)
