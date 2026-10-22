"""Prepare independent outcome-free directions; never alter the running pilot."""
import hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'log/20261022/tggates_rna_feedback_pilot'
FILES=['research/REPORT.md','log/20261022/api_evidence_innovation/DECISION.md',
       'log/20261022/rsi_later_task_literature/DECISION.md',
       'log/20261022/tggates_functional_qualification/clock_observability/REPORT.md',
       'log/20261022/tggates_rna_feedback_pilot/REVIEW_DECISION.md',
       'log/20261022/tggates_rna_feedback_pilot/APPLICATION_SCOPE_NOTE.md',
       'log/20261022/tggates_rna_feedback_pilot/STATE_CONTRIBUTION_READING_RULE.md']
ROLES={'next_mechanism_constructive':'建设方：从已失败方向以外寻找至多一个最小机制。必须给精确定义/方程、普通解释最强版本及一个能区分两者的反例或可测预测。',
       'next_mechanism_skeptic':'反方：独立判断还有什么值得尝试；至多提出一个机制，同时优先尝试构造与普通直接预测、元学习、最优实验设计、持续学习或程序搜索的等价实现。没有区别就明确NO_GO。',
       'next_mechanism_operational':'应用与数据方：独立从已认证数据和实际决策出发，至多提出一个有真实反馈菜单的机制；逐项列出观测、任务单位、成本、独立性、缺失证据及最低可运行实验。'}

def main():
    context='';hashes={}
    for name in FILES:
        raw=(ROOT/name).read_bytes();hashes[name]=hashlib.sha256(raw).hexdigest()
        context+='\n\n--- '+name+' ---\n'+raw.decode('utf-8')
    common=('只依据所附已存证据，最多2000中文字符。当前RNA实验仍未有结果，不能预测/捏造结果、改阈值、重跑停止分支、开启later14/AZ413reserve，也不能把待采集观测当已有数据。'
            '目标仍是有生物实质差异的虚拟细胞+研究程序改进机制，而非重命名标准算法。无可信候选是允许的结论。'
            '先列排除的最邻近历史失败或文献，再给机制、具体应用、可获得数据与缺口、可证伪创新主张、最小成功/停止条件。'
            '逐一说明world/agent/继承/联合/C4如何独立归因；可以指出本轮不应测试其中某项，但不得把它写成完成。'
            '必须面对强同信息直接预测/普通重训/CL/AL/简单混合/等预算搜索，不以通用逼近能力代替实际等价论证；也不以模块名字制造新颖性。'
            '文献链接仅是前轮审查记录；未提供原文的细节标未核实，不编造新引用。不要给任意临床阈值或未验证样本量。'
            '本轮是独立首评，没有其他评审输出；后续会真正交换原文交叉质疑。\n')
    for role,position in ROLES.items():
        dest=P/'api_reviews'/role;dest.mkdir()
        with (dest/'PROMPT.md').open('x',encoding='utf-8') as f:f.write(position+common+context)
    with (P/'NEXT_MECHANISM_REVIEW_EVIDENCE.json').open('x',encoding='utf-8') as f:
        json.dump(dict(status='INDEPENDENT_PROMPTS_PREPARED_NO_CANDIDATE_PROMOTED',files_sha256=hashes,
                       roles=list(ROLES),pilot_unchanged=True,new_biological_outcomes_read=False,
                       locator_failures=['Nonexistent tggates_mechanism_review/DECISION.md and tggates_clock_observability/DECISION.md; corrected via rg --files to actual nested clock report.']),f,indent=2)
    print(json.dumps(dict(status='PREPARED',roles=list(ROLES))))

if __name__=='__main__':main()
