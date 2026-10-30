"""Register inspected originals through the installed reference-library interface."""
from pathlib import Path
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

here = Path(__file__).resolve().parent
script = Path(r"D:\CodexData\.codex\skills\lit-survey\scripts\reference_library.py")
src = here / "sources/root"
reap = ET.parse(src/"reap_jats.body").getroot()
authors = "; ".join(" ".join(n.itertext()) for n in reap.findall('.//front/article-meta/contrib-group/contrib/name'))
papers = [
 ("cvpr2026-zeng-label-what-matters", "Label What Matters: Modality-Balanced and Difficulty-Aware Multimodal Active Learning",
  "Yuqiao Zeng; Xu Wang; Tengfei Liang; Yiqing Hao; Yi Jin; Hui Yu", "", "CVPR2026 pp29391-29399", "2026",
  "https://openaccess.thecvf.com/content/CVPR2026/html/Zeng_Label_What_Matters_Modality-Balanced_and_Difficulty-Aware_Multimodal_Active_Learning_CVPR_2026_paper.html",
  "rl_mba_pdf_full.body", False, "main", "Coordinator: PDF p1 and pp3-5, formulation, actual annotation action, validation and reward, REINFORCE. Results/SI not audited."),
 ("acl2026-long-1619", "Reasoning While Asking: Transforming Reasoning Large Language Models from Passive Solvers to Proactive Inquirers",
  "Xin Chen; Feng Jiang; Yiqian Zhang; Hardy Chen; Shuo Yan; Wenya Xie; Min Yang; Shujian Huang", "", "ACL2026 long.1619", "2026-07",
  "https://aclanthology.org/2026.acl-long.1619/", "asking_pdf.body", False, "main",
  "Coordinator: PDF p1 and pp3-5, teacher uncertainty/NLL, SFT trajectories, US-GRPO masking and rewards. Not full-paper reading or reproduced interaction."),
 ("doi-10.1038-s41467-026-76264-2", "Rank-guided learning accelerates automated enzyme engineering",
  authors, "10.1038/s41467-026-76264-2", "PMID42706258; PMC13550471", "2026-08-03",
  "https://doi.org/10.1038/s41467-026-76264-2", "reap_jats.body", False, "supplement",
  "Coordinator: formal JATS Sec3,4,12-16,26 and license. RankReg, frozen backbone/head, ensemble/UCB, experimental loop and training/validation counts; not full SI/code. JATS stored as supplement by library format contract, not a PDF."),
 ("doi-10.1073-pnas.1403080111", "Exploiting polypharmacology for drug target deconvolution",
  "Taranjit Singh Gujral; Leonid Peshkin; Marc W. Kirschner", "10.1073/pnas.1403080111", "PMID24707051; PMC3977247", "2014-03-19",
  "https://pmc.ncbi.nlm.nih.gov/articles/PMC3977247/", "polypharmacology_pmc_html.body", True, "main",
  "Coordinator: s3 principal-variable selection; main s5 deconvolution/collinearity paragraph; s6 siRNA validation paragraphs; s8/s10 assumptions and concentration. Worker separately read s3,s5-8,s10. No reproduction. Foundational closest prior, outside recent-paper window.")]
log = []


def run(args):
    r = subprocess.run([sys.executable, str(script), *args], capture_output=True, text=True, encoding="utf-8")
    log.append({"args":args,"exit_code":r.returncode,"stdout":r.stdout,"stderr":r.stderr})
    (here/"registration_log.json").write_text(json.dumps(log,indent=2)+"\n",encoding="utf-8")
    if r.returncode: raise SystemExit("Registration failed; inspect saved log, no automatic retry")


for pid, title, names, doi, alt, date, landing, filename, html, role, scope in papers:
    run(["record","reference","paper",pid,f"title={title}",f"authors={names}",f"doi={doi}",f"alt_id={alt}",
         f"formal_date={date}","date_basis=Verified official publication identity; see episode receipts for exact date resolution",
         f"landing_page={landing}","reading_level=P",f"reading_scope={scope}",
         "note=Original retrieved lawfully by coordinator; local-file helper source is not user-supplied. Exact URL/hash/status in research/2026-10-29-functional-mechanism-reopening/sources/root/retrieval.jsonl. No third-party original is included in GitHub publication."])
    run(["paper","reference",pid,"--file",str(src/filename),"--role",role] + (["--html"] if html else []))
    if role == "main":
        run(["record","reference","paper",pid,"reading_level=P",f"reading_scope={scope}"])
    run(["record","reference","code",pid,"download_status=not_verified",
         "note=Code execution/reproduction not performed in this targeted source pass; inspected reading scope and any official links remain in episode notes."])
print(json.dumps({"registered_papers":len(papers),"commands":len(log),"all_exit_zero":True}))
