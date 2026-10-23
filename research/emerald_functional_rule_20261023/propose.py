"""Ask for one finite mechanism/test on genuinely new functional data."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT = ROOT / 'log/20261023/emerald_functional_rule/api'
PROMPT = '''你是药物发现科研方法建设者。请提出至多1个精确、可证伪的功能反馈共享规律，或在没有合格机制时提出1项值得立刻运行的有限真实数据诊断。不要代码，不虚构文献/数据。你无检索能力。
新且尚未读数值的官方EmeraldBay公开源：52癌细胞line，93条件，其中44单药剂量条件涵19单药，47组合，2对照。4992rows/4836unique(line,condition)，52keys各4rows，summary无sample/plate/run。五日MOSAIC pooled cell-count proportions衍生growth_rate（精确公式/absolutecalibration未认证）。同终点RNA存在但未下载。仅能声称released relative phenotype预测，不能套Bliss/Loewe的survival单位或把52line当52独立湿实验。
强直接先例：2026Rhaister官方实现ALS additive cell+drug effects，再以source contexts中support功能向量→query功能dual ridge；target新context给support功能。supportRNA feature ridge也已实现。完整feature默认MLP另读query实测RNA，不能当support-only，作者具体R²run配置未核。所有新机制对手须同信息同预算，剂量/药物整组留出，source-only调参；conditionalEB、nonlinear direct、same-forward MAP/refit、meta/end-to-endquery训练、simplemixture、ordinaryAL/程序搜索不能弱化。
历史已停：sharedpotencyshift support最小二乘=ordinarysameforwardMAP；signedmean update=rankoneEB；Jaaks同target substitution真实interaction负结果；AZ mono effect coordinates输strongdirect；CDK组成小益无function益；Broad16lineRNA仅3.47%MSE，top10排序不及geneprior。不得重开旧labels改gate。不能因属于常规家族就宣称不可能创新，但精确等价solver不应安排胜自己。
这次希望用真实single/combination功能反馈找到可重复的改进对象，优先确认：少量组合反馈在已知全部单药后，能否纠正其他药物对的context-specific响应误差？fixedpair同dose插值不是crossdrug。当前菜单示例Adagrasib+Galunisertib、Sotorasib+Galunisertib、Sotorasib+LY3200882；药理标签只是待认证线索。不要为这些例子凭空假定可靠作用等价。全menu身份可获取，但你未见完整菜单所以不得断言覆盖。
1800中文字符内回答：一个<=6行公式的操作/规律（或NONE）；它何以有超强普通方法的可测样本/成本/科学贡献，最强替代解释；合法信息与整物理池采购单位；一项最多4种ordinary配置的最小真实诊断，如何先冻结discovery/confirmation防endpointfishing；成功/失败/停止条件，不导入旧任意5%；若无新机制如何得出有意义有限决策。分清功能预测、agent/update继承、G1/G0后代RSI，不把普通ridge正结果升级。'''

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    receipt_path = OUT / 'RECEIPT.json'
    assert not receipt_path.exists()
    (OUT / 'PROMPT.md').write_text(PROMPT, encoding='utf-8')
    receipt = dict(status='INITIATED', start=datetime.now(timezone.utc).isoformat(), logical_requests=1,
        prompt_sha256=hashlib.sha256((OUT / 'PROMPT.md').read_bytes()).hexdigest(),
        transport_attempts='NOT_EXPOSED', generated_code_executed=False)
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=180.))
    try:
        response = client.complete([dict(role='system', content='提出可执行科研判断，不虚构创新和验证。'),
            dict(role='user', content=PROMPT)], temperature=.7, max_tokens=7000, thinking_enabled=True)
        (OUT / 'PROPOSAL.md').write_text(response.content, encoding='utf-8')
        receipt.update(status='RESPONSE_RETAINED', model=response.model, finish_reason=response.finish_reason)
    except Exception as exc:
        receipt.update(status='FAILED_RETAINED', error_type=type(exc).__name__, error_code=getattr(exc, 'code', None))
    finally:
        receipt.update(end=datetime.now(timezone.utc).isoformat(), provider_usage=client.provider_usage)
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))
