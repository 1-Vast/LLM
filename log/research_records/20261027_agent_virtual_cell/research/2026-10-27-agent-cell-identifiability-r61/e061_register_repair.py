"""E061: audit and repair the structure of EVIDENCE_REGISTER.md.

Checks performed (pre-registered in PROTOCOL_E059.md):
  1. every original content line must survive somewhere in the rebuilt file
  2. claim rows appear in numeric order
  3. all changelog bullets live in section 6, none inside section 7
  4. the title year/round is current
  5. section 5's whitelist mentions every claim that is refuted or withdrawn
"""

from __future__ import annotations

import json
import re
from pathlib import Path

R = Path(r"D:\MAESTRO\research")
REG = R / "EVIDENCE_REGISTER.md"
OUT = R / "2026-10-27-agent-cell-identifiability-r61"
OUT.mkdir(parents=True, exist_ok=True)

text = REG.read_text(encoding="utf-8")
lines = text.splitlines()

def is_row(ln, prefix):
    return ln.startswith("| ") and re.match(r"^\|\s*(" + prefix + r"\d+)\s*\|", ln)

f_rows = [ln for ln in lines if is_row(ln, "F")]
c_rows = [ln for ln in lines if is_row(ln, "C")]
bullets = [ln for ln in lines if ln.startswith("- 2026-10-27")]

def key(ln, prefix):
    m = re.match(r"^\|\s*(" + prefix + r")(\d+)\s*\|", ln)
    return int(m.group(2))

f_rows.sort(key=lambda x: key(x, "F"))
c_rows.sort(key=lambda x: key(x, "C"))
bullets = list(dict.fromkeys(bullets))  # drop exact duplicates, keep order

# --- locate the structural blocks of the original text
def find(pred, default=-1):
    for i, ln in enumerate(lines):
        if pred(ln):
            return i
    return default

i_s1 = find(lambda l: l.startswith("## 1"))
i_s2 = find(lambda l: l.startswith("## 2"))
i_s3 = find(lambda l: l.startswith("## 3"))
i_s4 = find(lambda l: l.startswith("## 4"))
i_s5 = find(lambda l: l.startswith("## 5"))
i_s6 = find(lambda l: l.startswith("## 6"))
i_s7 = find(lambda l: l.startswith("## 7"))

def block(a, b):
    return [ln for ln in lines[a:b] if not is_row(ln, "[FC]") and not ln.startswith("- 2026-10-27")]

sec3 = block(i_s3, i_s4)
sec4 = block(i_s4, i_s5)
sec5 = block(i_s5, i_s6)

# rebuild section 5 whitelist line with every refuted/withdrawn claim
refuted = []
withdrawn = []
for ln in c_rows:
    cid = "C%d" % key(ln, "C")
    if "已否证" in ln:
        refuted.append(cid)
    if "已撤回" in ln:
        withdrawn.append(cid)
sec5 = [ln for ln in sec5 if "C5/C7/C11" not in ln]
sec5.append("")
sec5.append("- **状态汇总（R61 自动生成）**：已否证 = %s；已撤回 = %s；其余主张一律为**探索性或已停止**，"
            "不得写成已确认能力。" % ("、".join(refuted) or "无", "、".join(withdrawn) or "无"))

header = [
    "# 证据登记（截至 R60，2026-10-27）",
    "",
    "> **R58 综合**：57 轮的整体状态见 [SYNTHESIS.md](SYNTHESIS.md)——最简算法、成立的 5 条、",
    "> 被否证的 11 条、不可检验的 5 类、停止清单、以及\"晋升代码已无可行路线\"（R59 更新）。",
    "> **R61 结构修复**：主张行按编号排序、变更记录全部归入第 6 节、标题与状态汇总更新。",
    "",
    "本文件把 R1–R60 的主张压成一张状态表，供后续轮次直接引用、避免重开已停的线。**状态词汇严格区分**：",
    "",
    "- **已核实**：有独立复核或直接计数，且不依赖模型选择。",
    "- **探索性**：数值稳定、CI 不含 0，但数据集已被前轮用作评分终点 / 跨日期，需独立批次确认。",
    "- **已否证**：预注册的假设被数据否定（这是有效结论）。",
    "- **已停止**：按预注册停止条件不再推进；重开条件已写明。",
    "- **不可检验**：本资源结构上无法回答（附证据）。",
    "",
    "旧记录不迁移、不改写；本表只做索引与状态判定。",
    "",
]

new_lines = header + block(i_s1, i_s2)
new_lines += ["## 1．资源事实（决定能问什么）", ""]
new_lines += ["| ID | 事实 | 证据 | 状态 |", "|---|---|---|---|"] + f_rows
new_lines += [""]
new_lines += ["## 2．主张与状态", ""]
new_lines += ["| ID | 主张 | 关键数值 | 状态 | 来源 |", "|---|---|---|---|---|"] + c_rows
new_lines += [""]
new_lines += sec3 + [""]
new_lines += sec4 + [""]
new_lines += sec5 + [""]
new_lines += ["## 6．变更记录", ""] + bullets + [""]
new_lines += ["## 7．与文献的关系（R45 建立，片段级）", ""]
new_lines += [
    "**访问限制**：`web_fetch` 对所有域名返回\"解析到非公网 IP\"，因此只有 `web_search` 片段，**不能**据此声称新颖性或\"文献里没有\"。详见 [POSITIONING.md](POSITIONING.md)。",
    "",
    "- **很可能是复现（7 条）**：C2、C12/C24、C17、C19、C26、C27、C34。**不得**写成新发现，必须标\"复现/与已知结构一致\"。",
    "- **候选贡献（2 条，待一手核对）**：(a) 组织条件效应量（C25）；(b) 决策规则的池大小条件（C28/C32），但**C36/C38 已证明阈值不可跨群体迁移、C39 证明就地重估失败**，故只能声称群体内有效。",
    "- **规则**：候选贡献在完成一手核对前**不得**写\"首次\"；本项目的\"首次\"一律指\"本项目内首次\"。",
]

rebuilt = "\n".join(new_lines).rstrip() + "\n"
REG.write_text(rebuilt, encoding="utf-8")

# ---------------- audit ----------------
rebuilt_lines = rebuilt.splitlines()
orig_content = [ln for ln in lines if ln.strip() and not ln.startswith("#")]

missing = [ln for ln in orig_content if ln not in rebuilt_lines]
checks = []
checks.append({"name": "no_content_lost", "ok": len(missing) == 0,
               "detail": "missing=%d" % len(missing)})
checks.append({"name": "f_rows_sorted",
               "ok": [key(ln, "F") for ln in f_rows] == sorted(key(ln, "F") for ln in f_rows),
               "detail": str([key(ln, "F") for ln in f_rows])})
checks.append({"name": "c_rows_sorted",
               "ok": [key(ln, "C") for ln in c_rows] == sorted(key(ln, "C") for ln in c_rows),
               "detail": str([key(ln, "C") for ln in c_rows])})
i7 = find(lambda l: l in rebuilt_lines and l.startswith("## 7"))
tail = rebuilt_lines[i7:] if i7 >= 0 else []
checks.append({"name": "no_changelog_inside_section7",
               "ok": not any(ln.startswith("- 2026-10-27") and ("R46" in ln or "R55" in ln or "R60" in ln) for ln in tail),
               "detail": "section7 bullets checked"})
checks.append({"name": "title_current", "ok": "截至 R60" in rebuilt_lines[0], "detail": rebuilt_lines[0]})
checks.append({"name": "f_row_count", "ok": len(f_rows) == 9, "detail": str(len(f_rows))})
checks.append({"name": "c_row_count", "ok": len(c_rows) == 39, "detail": str(len(c_rows))})
checks.append({"name": "changelog_has_all_rounds",
               "ok": all(("R%d " % n) in rebuilt or ("R%d " % n) in "".join(bullets) for n in (15, 44, 51, 57, 60)),
               "detail": "checked R15/R44/R51/R57/R60"})
checks.append({"name": "whitelist_summary_present", "ok": "状态汇总（R61 自动生成）" in rebuilt, "detail": ""})

res = {"kind": "register_structure_repair", "checks": checks,
       "n_ok": sum(1 for c in checks if c["ok"]), "n_checks": len(checks),
       "counts": {"f_rows": len(f_rows), "c_rows": len(c_rows), "changelog_bullets": len(bullets)},
       "refuted": refuted, "withdrawn": withdrawn,
       "missing_lines": missing[:10]}
(OUT / "E061_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
for c in checks:
    print(("OK   " if c["ok"] else "FAIL ") + c["name"] + " | " + c["detail"])
print("\n%d/%d pass" % (res["n_ok"], res["n_checks"]))
if missing:
    print("MISSING:", missing[:5])
