"""One bounded request for a distinct reusable error correction; no generated code."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT = ROOT / 'log/20261023/reusable_error_mechanism/api'
PROMPT = '''你是科研构造者。不是再提框架，而是构造至多一个精确、可被反例推翻的反馈更新限制。你无检索工具，不得捏造文献或数据。限1800中文字符，不输出代码。
目标：真实细胞干预状态/功能反馈改进后续药物决策，最后才检验规则继承和更好的改进策略。普通数学完全允许；属于已知家族不是否定理由，但必须指出相比具体强ordinary操作的新性质/样本或总成本理由。
当前实证：一个K562 CRISPRa源，单/双RNA与功能；普通RNA条件功能补全14–16%MSE增益但约9.77倍拟合时间，非新算法、非跨背景继承。Norman73双扰动对角混合曲率law输强direct ridge2.96%，已停不能调基因/头/空间救分。Emerald36已曝背景44单药功能→15组合条件普通ridge比源均值MSE好56%，不同信息；再加固定anchor MSE坏.91%，regret好4.76%，联合门失败，16保留背景禁止打开。只有released相对growth_rate，不能假定Bliss生存标度。CDK中期组成及真实终末IC50已试，功能无稳健增益，不能称未试。AML/ALL身份映射缺失入口已停。
已停且不能换名：sharedpotencyshift=jointWLS/MAP，signedmean=EB；功能scalar actuation calibration=ridge且旧置信box随n缩0不一致；固定positivequadratic潜能的实际reciprocity不成立；共享kernel混合/广泛geneprior调参；裸冻transport更新survival=同law反应输运推断，终点组成混淆转移/选择/分裂。DiscoRL已有learned recurrent targets+ordinary innerKL+outerreturn，单改细胞名字无新意。普通计数误差模型、survivor/capture校正、主动学习、元优化、densityratio本身也非创新。
请独立找一个不同于上面停止配置的可复用错误模式。给<=6行完整公式：什么可观察反馈、共享/不共享什么量、精确更新；强同信息direct/ordinary union refit/episodic conditional/meta learner为什么可能有限预算低效；最强简单替代解释；一个不需要新数据的最小合成反例/一致性或等价检查（只检验操作，不冒充生物）；一个可在现有已曝source诚实探索且不重启旧菜单的最小功能实验设想。若无足够具体机制则NONE并给一个有信息量的理由，不靠新名词交卷。不要要求直接模型原则上不能表达，不要靠虚构新资产或未来湿实验填空。'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    receipt_path = OUT / 'RECEIPT.json'
    assert not receipt_path.exists(), 'Inspect the existing handle instead of duplicating a call'
    prompt_path = OUT / 'PROMPT.md'
    prompt_path.write_text(PROMPT, encoding='utf-8')
    receipt = dict(status='INITIATED', utc=datetime.now(timezone.utc).isoformat(),
                   logical_requests=1, transport_attempts='NOT_EXPOSED',
                   prompt_sha256=hashlib.sha256(prompt_path.read_bytes()).hexdigest(),
                   generated_code_executed=False, biological_outcomes_read=0)
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    client = DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT), timeout_seconds=180.))
    try:
        response = client.complete([dict(role='system', content='Construct one precise mechanism and actively seek its falsifier.'),
                                    dict(role='user', content=PROMPT)],
                                   temperature=.7, max_tokens=10000, thinking_enabled=True)
        (OUT / 'PROPOSAL.md').write_text(response.content, encoding='utf-8')
        receipt.update(status='RESPONSE_RETAINED', model=response.model, finish_reason=response.finish_reason)
    except Exception as error:
        receipt.update(status='FAILED_RETAINED', error_type=type(error).__name__, error_code=getattr(error, 'code', None))
    finally:
        receipt.update(ended_utc=datetime.now(timezone.utc).isoformat(), provider_usage=client.provider_usage)
        receipt_path.write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
