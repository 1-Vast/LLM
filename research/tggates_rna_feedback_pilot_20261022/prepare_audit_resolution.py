"""Bind empirical full-loop synthetic evidence to the two disputed audit claims."""
from pathlib import Path
import json,hashlib
P=Path('log/20261022/tggates_rna_feedback_pilot');C=Path(__file__).resolve().parent
d=P/'api_reviews/implementation_resolution';d.mkdir(exist_ok=True)
smokes=sorted((P/'synthetic_tests').glob('full_pipeline_*/TEST_ASSERTIONS.json'))
assert len(smokes)==1
smoke=smokes[0].parent
receipt=json.loads((smoke/'NUMERICAL_RECEIPT.json').read_text())
source=(C/'run_pilot.py').read_text(encoding='utf-8')
prompt='仅审查以下两项争议，回答不超过1000中文字符，不要展开逐行源码、不编造bug。先前审查有多次自我撤回且length截断，不能视为已通过。\n'
prompt+='1. 审查称final只有rho0造成4332fits。但selected按family逐一选，实际family是rho_0/rho_0.5/rho_1/direct/no_rna/four_gene/rbf/refit八个，final三rho各2=6,四direct各1=4,七dev refit各3=21, null3。base1806+source2496+final31+null3=4336。已对同一未改run代码执行完整24source/7dev/64config synthetic smoke，devHigh都NaN，实际receipt如下。是否撤回错误4332判断？\n'
prompt+=json.dumps(receipt,ensure_ascii=False)+'\n'
prompt+='2. 审查要求删fixed_half_mixture才算ordinary。但原冻结安排是比较简单混合，固定50/50(candidate+selecteddirect)全程计入最强替代基线。这是预先选择的更严格gate，不是数据泄漏。rho0exact copy是同一程序所以merged，mixture是不同程序非同构。此时是否仍有必须排除的统计理由？不得因它更严而事后放松门槛。可以指出名称ordinary不精确，区别数学bug vs保守比较选择。\n'
prompt+='实际selected及final循环摘录：\n'+source[source.index('        selected={}'):source.index('        nulls={}')]+'\n'
prompt+='允许明确反对root，但须给可复现事实。其余候选不具独特算法新颖性、单N和开发暴露等局限保持。完整smoke不是实证性能证据，仅数值程序和计数。\n'
with (d/'PROMPT.md').open('x',encoding='utf-8') as f:f.write(prompt)
with (d/'BOUND_EVIDENCE.json').open('x') as f:json.dump({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [smoke/'NUMERICAL_RECEIPT.json',smoke/'TEST_ASSERTIONS.json',C/'run_pilot.py']},f,indent=2)
