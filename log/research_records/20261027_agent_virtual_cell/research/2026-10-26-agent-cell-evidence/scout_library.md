# Scout 来源入库与核验账本

2026-10-26 14:40—14:43 UTC。复用 `D:/MAESTRO/reference`；仅补入已读三篇，不增加 query、不扩大 pass、不运行实验、不安装、不取源码。requested_model=gpt-6.1-sol，requested_effort=high，effective_model/effort=unknown。未更改其他研究产物；README 原有五篇统计保留，只末尾追加增量与协调者更新提示。

执行环境：`D:/anaconda/envs/maestro/python.exe -X utf8 -I D:/CodexData/.codex/skills/lit-survey/scripts/reference_library.py`。表格全部由该脚本维护，没有手写 papers.tsv/repositories.tsv。

## 三篇原始正文

| paper_id | 原始题名与来源 | 本地保存、字节数、SHA-256前12位 | 实际阅读范围 |
|---|---|---|---|
| arxiv-2602.05340 | Decision-Focused Sequential Experimental Design: A Directional Uncertainty-Guided Approach；https://arxiv.org/html/2602.05340v1；v1=2026-02-05 | `reference/papers/arxiv-2602.05340/paper.html`；837570；`16ca115a18df` | P；摘要；§1.1（web L91—129）；§2.2/Algorithm 1（L182—228）；未核证明与数值结果。 |
| arxiv-2605.26093 | Goal-driven Bayesian Optimal Experimental Design for Robust Decision-Making Under Model Uncertainty；https://arxiv.org/html/2605.26093v1；v1=2026-05-25 | `reference/papers/arxiv-2605.26093/paper.html`；641354；`954efcd0f3ca` | P；摘要；§2.1—§3.3（web L126—169）；Appendix H.1—H.2（L841—861）；未核数值结果与实现。 |
| arxiv-2603.14094 | Maximin Robust Bayesian Experimental Design；https://arxiv.org/html/2603.14094v1；v1=2026-03-14 | `reference/papers/arxiv-2603.14094/paper.html`；836130；`4b72f6f7b8a2` | P；摘要；§3.1—§3.2（web L113—174）；未核 PAC-Bayes 证明。 |

保存的是公开 HTML 正文，三篇均 downloaded_html；下载不代表 F 级通读。第一作者分别是 Beichen Wan、Jinwoo Go、Hany Abdulsamad。下载脚本的自动 identity_check 均报告 title found、first author found，且含 method/result/reference。随后实际解析本地 title/h1，三个标题均与已读原始页面一致，第一作者均找到。三篇均按 preprint 登记，不推断同行评议状态。

## 命令及结果

1. 对三个 paper_id 分别执行 `record LIB paper PAPER_ID`，写入已核 title/authors/doi/alt_id/v1日期/来源 URL、reading_level=P 与上表精确 reading_scope；三次退出0。新建题录时脚本生成源码检查行。
2. 对三个 ID 串行执行 `paper D:/MAESTRO/reference PAPER_ID https://arxiv.org/html/IDv1 --html --version arxiv-v1`；三次退出0，返回 downloaded_html。未绕过访问限制；无恢复重试。
3. 使用标准库 HTMLParser 只读本地 title/h1，核对题名及第一作者；三篇均匹配。未运行论文源码。
4. 对三个 ID 分别执行 `record LIB code PAPER_ID download_status=not_verified`，note 明确 code availability/ownership 未核，无源码下载或执行；三次退出0。未将未核写成 not_found 或 not_public。
5. `verify D:/MAESTRO/reference --json` 退出0，完整快照如下。

```json
{
  "papers": {"unique": 8, "files": 4, "downloaded_html": 4, "restricted": 4},
  "code_rows": {"not_verified": 8},
  "papers_with_official_code_stored": 0,
  "snapshots": 0,
  "changed_snapshots": [],
  "megabytes": {"papers": 2.6, "code": 0.0},
  "errors": [],
  "warnings": []
}
```

下一决定只留给协调者：合并本轮来源后更新 README 顶部边界与 Counts；本文件不再提出机制建议。此前五篇的原始统计未删除或覆盖。
