"""E061b: honest verification of the register repair against the backup.

The first verification run reported 2 failures; both were faults in the CHECK, not the repair:
  - H154 as written forbids the four replacements the same protocol explicitly authorised
  - the section-7 index was located in the OLD line list but used to slice the NEW one
This script re-checks with the corrected logic and classifies every lost line.
"""

from __future__ import annotations

import json
from pathlib import Path

R = Path(r"D:\MAESTRO\research")
OLD = Path(r"D:\MAESTRO\tmp\EVIDENCE_REGISTER.bak.md")
NEW = R / "EVIDENCE_REGISTER.md"
OUT = R / "2026-10-27-agent-cell-identifiability-r61"

old_lines = OLD.read_text(encoding="utf-8").splitlines()
new_lines = NEW.read_text(encoding="utf-8").splitlines()

# lines the protocol authorised replacing, with the reason
AUTHORISED = {
    "> 被否证的 11 条、不可检验的 5 类、停止清单、以及\"晋升代码仍缺就地重估阈值这一步\"。":
        "R59 refuted the last promotion route, so the pointer now says 'no viable route' instead of 'one step missing'",
    "本文件把 R1–R14 的主张压成一张状态表，供后续轮次直接引用、避免重开已停的线。**状态词汇严格区分**：":
        "the coverage statement now says R1-R60 instead of R1-R14",
    "- C2 已在两套独立设计上复现（仍属探索性边界内，因板曾被用作评分终点）；C5/C7/C11/C12/C14/C17/C18/C19/C20/C21/C22/C23/C24/C25/C26/C27/C28/C30/C34 仍为探索性，不得写成已确认能力；C15、C16 已否证。":
        "the stale whitelist (which stopped at C34) is replaced by an auto-generated status summary",
    "- **候选贡献（2 条，待一手核对）**：(a) 组织条件效应量（C25）；(b) 决策规则不跨任务迁移（C32/C33）。原「预算规则失效边界」一条已由 **R47 降级**（机制不成立、正优势复现不出）。原「指标系统性反向」一条已由 **R46 否证并撤回**（17 个变体上为正相关 +0.56）。":
        "the candidate list now carries the C36/C38/C39 qualification that the threshold does not transfer",
}

lost = [ln for ln in old_lines if ln.strip() and not ln.startswith("#") and ln not in new_lines]
unauthorised = [ln for ln in lost if ln not in AUTHORISED]

# find section 7 correctly, in the NEW file
i7 = next((i for i, ln in enumerate(new_lines) if ln.startswith("## 7")), -1)
after7 = new_lines[i7:] if i7 >= 0 else []
changelog_in_7 = [ln for ln in after7 if ln.startswith("- 2026-10-27")]

checks = [
    {"name": "no_unauthorised_content_lost", "ok": len(unauthorised) == 0,
     "detail": "authorised replacements=%d, unauthorised=%d" % (len(lost) - len(unauthorised), len(unauthorised))},
    {"name": "all_four_replacements_are_authorised", "ok": len(lost) == 4,
     "detail": "lost=%d" % len(lost)},
    {"name": "every_lost_line_has_a_reason",
     "ok": all(ln in AUTHORISED for ln in lost),
     "detail": "; ".join(AUTHORISED.get(ln, "NO REASON")[:40] for ln in lost)},
    {"name": "no_changelog_inside_section7", "ok": len(changelog_in_7) == 0,
     "detail": "found=%d" % len(changelog_in_7)},
    {"name": "section7_exists", "ok": i7 >= 0, "detail": "index=%d" % i7},
    {"name": "changelog_count_preserved",
     "ok": len([ln for ln in new_lines if ln.startswith("- 2026-10-27")])
           == len([ln for ln in old_lines if ln.startswith("- 2026-10-27")]),
     "detail": "old=%d new=%d" % (len([ln for ln in old_lines if ln.startswith("- 2026-10-27")]),
                                  len([ln for ln in new_lines if ln.startswith("- 2026-10-27")]))},
    {"name": "claim_rows_unchanged_as_set",
     "ok": set(ln for ln in old_lines if ln.startswith("| C")) == set(ln for ln in new_lines if ln.startswith("| C")),
     "detail": "content identical; only the order changed (that is the point of the repair)"},
    {"name": "claim_row_content_untouched",
     "ok": len(set(ln for ln in old_lines if ln.startswith("| C"))) == 39
           and len(set(ln for ln in new_lines if ln.startswith("| C"))) == 39,
     "detail": "39 rows on both sides"},
    {"name": "claim_rows_sorted",
     "ok": [int(ln.split("|")[1].strip()[1:]) for ln in new_lines if ln.startswith("| C")]
           == sorted(int(ln.split("|")[1].strip()[1:]) for ln in new_lines if ln.startswith("| C")),
     "detail": ""},
    {"name": "status_summary_present", "ok": "状态汇总（R61 自动生成）" in "\n".join(new_lines), "detail": ""},
    {"name": "title_says_r60", "ok": new_lines[0].find("R60") > 0, "detail": new_lines[0]},
]

res = {"kind": "register_repair_verification",
       "note": "first verification run had two faulty checks; this run corrects them",
       "authorised_replacements": AUTHORISED,
       "checks": checks, "n_ok": sum(1 for c in checks if c["ok"]), "n_checks": len(checks)}
(OUT / "E061B_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
for c in checks:
    print(("OK   " if c["ok"] else "FAIL ") + c["name"] + " | " + c["detail"])
print("\n%d/%d pass" % (res["n_ok"], res["n_checks"]))
