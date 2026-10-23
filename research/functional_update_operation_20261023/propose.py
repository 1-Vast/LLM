"""One new API proposal grounded in completed functional experiment, no execution."""
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from src.agent.llm import DeepSeekChatClient, MAESTROSettings

OUT=ROOT/'log/20261023/functional_update_operation/api'
PROMPT='''你是科研机制建设者，提出至多一个精确更新操作(不是架构)，以真实功能实验反馈改进虚拟细胞/后续研究能力。允许NONE，不虚构论文/数据。你无检索能力。
最新实证：Broad2026选中100基因16癌line，实测扰动pseudobulk与外部历史Chronos依赖性标签配对。全部1593state×34648transcript已曝光；1523finite函数。规范源内嵌套，line/batch留出，gene prior+QC/panel-context(linear/RBF) restricted vs加target-specificRNA/ridge/RBF/50:50mixture full；MSE仅降3.47/3.59%，14/16同向，未达预先5%门，固定菜单STOP。top10regret full .08565甚至略差简单geneprior .08521。不得重拟这批标签、事后选G、降低门。该任务是已公开Chronos重构，不是药物疗效/前瞻发现。
历史失败：single inherited signedmean direction与同历史rankoneGaussian update等价且opposite signs抵消；Euclidean regularizer重参数化失稳；tangent control null非finite guarantee。噪声半径当绝对update bound随n变0已否。target-action calibration/frozen scalar ridge不是新操作。bareIFT/ShermanMorrison/conditionalcovariancekernel/PCA/mixture/LoRAgenerator/entropyTTT不能自动升级。已完成旧TG、Norman73pair、CDK、CXCL9、kinobeads、Jaaks scoped STOP，不可换名重启。
强ordinary：同历史 conditional empiricalBayes K(q)=Cov(query_error,support_residual|q)[Cov(support_residual|q)+R]^-1；direct episodic(state,support)->query；普通unionrefit/CL；真实functional query loss穿过更新训练meta-init；同预算BayesianAL/程序搜索。不能只比无信息全参数refit。前沿已有SCOUT共享belief actionoutcome+outerpolicy，CLAW context->LoRA联合world，HarnessTTT同parent后代credit，ExpEvolve因素抽取/UCB；TTT-E2E真正同目标postupdate outerloss。把这些换成细胞词无贡献。
寻找一个有细胞学理由的受限传播/更新规律：一条真实功能反馈究竟应纠正哪些未测干预/状态预测？何种合法前反馈信息能决定这种限制，何时强ordinary有限数据/成本下会系统错，简单限制怎样避免；不要给一堆可选gate/hypernetwork/ICL。用<=1800中文字符完整回答：精确公式/可继承对象；为何不等于明确ordinary；最强可能等价/失败反例；一个最小合成双向检验(含支持例和推翻例，同信息同成本)；所需新独立真实功能应用数据和STOP，不可把已读16line当确认；分开模型适应U1/U0与同base/history/budget编辑器G1/G0后代效用。若没有能自证区别的操作，请NONE并指出什么具体可观测关系缺失。不要代码，不要文献名堆砌。'''

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    receipt_path=OUT/'RECEIPT.json';assert not receipt_path.exists()
    (OUT/'PROMPT.md').write_text(PROMPT,encoding='utf-8')
    receipt=dict(status='INITIATED',start=datetime.now(timezone.utc).isoformat(),logical_requests=1,
                 prompt_sha256=hashlib.sha256((OUT/'PROMPT.md').read_bytes()).hexdigest(),
                 transport_attempts='NOT_EXPOSED',generated_code_executed=False)
    receipt_path.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    client=DeepSeekChatClient(replace(MAESTROSettings.from_workspace(ROOT),timeout_seconds=180.))
    try:
        response=client.complete([dict(role='system',content='精确而简洁的科研数学机制；给最强反对证据，不虚构验证。'),
                                  dict(role='user',content=PROMPT)],temperature=.7,max_tokens=7500,thinking_enabled=True)
        (OUT/'PROPOSAL.md').write_text(response.content,encoding='utf-8')
        receipt.update(status='RESPONSE_RETAINED',model=response.model,finish_reason=response.finish_reason)
    except Exception as exc:
        receipt.update(status='FAILED_RETAINED',error_type=type(exc).__name__,error_code=getattr(exc,'code',None))
    finally:
        receipt.update(end=datetime.now(timezone.utc).isoformat(),provider_usage=client.provider_usage)
        receipt_path.write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))
