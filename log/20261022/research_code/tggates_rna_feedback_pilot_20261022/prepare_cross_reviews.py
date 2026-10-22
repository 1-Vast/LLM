"""Build opposing cross-review requests from exact retained first opinions."""
from pathlib import Path
P=Path('log/20261022/tggates_rna_feedback_pilot')
for role,own,peer in [('method_cross','method_skeptic_v2','mechanism_advocate_v2'),
                      ('advocate_cross','mechanism_advocate_v2','method_skeptic_v2')]:
    d=P/'api_reviews'/role;d.mkdir(exist_ok=True)
    prompt='你继续承担上一轮独立立场。请明确回应另一方及root的判断：哪些支持、哪些反对、未决分歧以及最小后续验证。不要增加数据菜单。不是泛泛附和。\n'
    prompt+='你的首轮文本：\n'+(P/'api_reviews'/own/'RESPONSE.md').read_text(encoding='utf-8')
    prompt+='\n对方首轮文本：\n'+(P/'api_reviews'/peer/'RESPONSE.md').read_text(encoding='utf-8')
    prompt+='\nRoot在首轮评审之后、首次CEL读取之前冻结的裁决：\n'+(P/'NUMERICAL_AMENDMENTS.md').read_text(encoding='utf-8')
    prompt+='\n附新技术证据（不是结果选模）：第一源CEL已计算MAS5但QC accessor错误导致没有输出；核实affy源码后仅把se.exprs(calls)改成assayDataElement(calls,"se.exprs")。原代码/失败保留，未处理其余阵列。CDF使用原始未改manufacturer data环境native affy lookup，原namespace lazy-load失败，所有数值方法不变。对该最小技术修复有无科学合理性异议？\n'
    with (d/'PROMPT.md').open('x',encoding='utf-8') as f:f.write(prompt)
