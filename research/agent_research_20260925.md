# Agent-first research and optimization, 2026-09-25

## Research gate and scope

Research was completed before the implementation change described below. The user-supplied
drug-synergy landscape report is a source of candidate ideas, not an instruction to implement
its proposed architecture. The primary object of study is MAESTRO's scientific agent;
virtual-cell predictions are supporting tools, and learned multimodal fusion is conditional.

This is a targeted design review, not an exhaustive systematic review. It combines the report,
five primary full texts (selected methods, results and limitations), one recent agent abstract,
and a read-only reproduction of a repository defect. It does not reproduce the papers' training
experiments or establish biological effectiveness. Searches used Europe PMC and direct arXiv
retrieval on 2026-09-25. Search failures are not evidence that a work does not exist.

Raw responses, extracted text, search metadata and the pre-change reproduction are retained
locally in `outputs/agent_research_20260925/`. The version-controlled
[source record](knowledge/agent_research_sources_20260925.json) preserves URLs, raw-response
SHA256 hashes, selected verbatim passages, and failed retrievals. Unversioned arXiv URLs refer
to the retrieved snapshot; the hash identifies it, not an inferred manuscript version.

## Verified sources and limits

| Source | Access | Finding relevant to this task | Limit on transfer |
|---|---|---|---|
| [One-hot news: drug synergy models shortcut molecular features](https://doi.org/10.1093/bioinformatics/btag040), 2026 | Full text, PMC13005728; methods, split definitions, discussion | Replacing features with identity can preserve performance; evaluate unseen pairs, one unseen drug, both unseen drugs and unseen cells separately | Tests feature reliance within the published pipelines, with a disclosed MatchMaker dataset update; not a ranking of architectures. Its one-hot dictionary uses the union of train/test identities, which must be disclosed as transductive identity access |
| [SynVerse](https://doi.org/10.1093/bib/bbaf676), 2025 | Full text, PMC12753315; framework/results and ablations | Sixteen configured models; module removal, feature shuffling and weighted-degree-preserving rewiring challenge the claimed contribution of biological features | Sixteen configurations are not sixteen independently reproduced published SOTAs. Predictive shortcut results are not agent-policy measurements |
| [Reliable evaluation and learning in multi-input biological association prediction](https://doi.org/10.1093/bib/bbag376), 2026 | Full text, PMC13358880; degree-ratio argument and entity-balanced sampling | Overall class balance can conceal entity-level label imbalance. Audit entity statistics and evaluate alternative balanced sets | UnbiasNet's journal version supersedes citing only its preprint. Entity balancing targets a specified shortcut; it is not a universal guarantee against contamination or confounding |
| [BioDiscoveryAgent](https://arxiv.org/abs/2405.17631) | Full text snapshot; closed-loop methods, Tables 3/4, limitations | Observed perturbation outcomes guide later batches. Literature, gene search and critic benefits vary with the LLM; tools can hurt. Tabular pathway data can provide information absent from text | Generic research loops and critics already have precedent. Reported perturbation hit rates cannot be transferred to MAESTRO; cell coverage and early/late-round differences matter |
| [ScienceAgentBench](https://arxiv.org/abs/2410.05080) | Full text snapshot; evaluation and contamination controls | 102 tasks from 44 publications; assess executable outputs and cost. In its tested setup, a simpler self-debug agent outperformed a more elaborate framework | Some figure evaluations use an LLM judge; the benchmark is not wholly deterministic. Its specific performance/cost ratios are not universal architecture laws |
| [Autonomous biomedical research with an artificial intelligence agent](https://doi.org/10.1126/science.adz4351), Biomni, 2026 | Europe PMC metadata and abstract only, PMID 42424436 | Supports studying retrieval-assisted tool discovery, planning and execution across heterogeneous biomedical tasks | No full-text methods or numerical performance claims are relied on here |

The report's DDIAgents and MoAgent references were not independently resolved in the available
searches. A 2026 DrugAgent virtual-screening paper was found, but it is a different title/year
from the report's DrugAgent reference and cannot substitute for it. Knowledge-graph-agent
full-text retrieval returned HTTP 500; co-scientist HTML returned 404; arXiv search API calls
returned 406. None of these works supports an implementation decision in this pass.

## Report corrections and design implications

1. **Evaluation before model expansion.** One-Hot News, SynVerse and UnbiasNet support testing
   shortcuts and feature contribution. They do not establish that an LLM or GNN is always
   superior. Freeze the agent's data, model, tool catalogue, outcomes and budget before
   comparing policies. Separate pair, drug, cell, study and time generalization as applicable.
2. **Tools need incremental utility.** BioDiscoveryAgent's tool ablations contradict assuming
   that adding a retrieval agent or critic necessarily helps. Compare no critic, no virtual
   cell, fixed workflow, one-shot selection and bounded feedback on the same underlying cases.
   Jev's probabilities are advisory outputs, not measured premises or calibrated truth.
3. **Check behavior, not just fluent explanations.** Following ScienceAgentBench's evaluation
   approach, assess actual tool calls, admissible choices, evidence import, repair, stop reasons
   and resource consumption. Hide outcome labels outside agent-readable assets for formal
   evaluation. Pretraining contamination remains an additional limitation.
4. **No unsupported novelty claim.** Generic multi-agent orchestration, retrieval, criticism and
   multimodal fusion have substantial precedent. MAESTRO's candidate contribution is a testable
   policy for evidence-bounded mechanism investigation and repair, not their mere combination.
5. **Architecture sketches are not experiments.** Empty experimental subsections in the supplied
   report cannot establish module effectiveness. Claims of guaranteed originality, universal
   superiority, or causal interpretation from attention should not enter the project claim.
6. **Preserve scientific distinctions.** A prediction is not a perturbation experiment; RNA,
   protein abundance, target engagement, activity and viability are different quantities.
   Regulatory association is not automatically causation. Matched interventions, controls and
   independent functional evidence are needed to discriminate proposed mechanisms.

## Multimodal and multiscale strategy

The agent requests qualified tools and reasons over their evidence records. Numeric matrices
remain in artifacts and appropriate numerical tools. Each result must retain quantity,
sample/independent unit, organism/cell context, dose/time, control, batch, missingness, source,
processing version and prediction/measurement status. An absent modality is not zero, and
unpaired cohorts cannot be silently presented as paired single-cell measurements.

Choose modalities by the unresolved hypothesis: RNA may support a transcriptional response;
matched chromatin can support accessibility-related hypotheses; activity or occupancy may
discriminate a target-function question. More modalities alone do not make a decision better.
Compare the added modality against its access, processing, inference and new-measurement costs.
Public access can be inexpensive while prospective proteomics or perturbation screens are not.

Within-scale numerical models remain optional tools. Across scales, use explicit identity,
membership or experimentally qualified mapping contracts; propagate uncertainty across estimated
bridges. Neither gene-to-protein identity nor pathway membership establishes activity, tissue
phenotype or clinical safety. Context-specific signed GRN assertions may suggest which
measurement distinguishes compensation from inadequate perturbation. This is a biological
reason for choosing evidence, not a claim that an attention gate implements regulatory feedback.

Keep the existing State adapter as a scoped prediction/refusal tool. A refusal should lead to an
alternative registered evidence route or justified deferral. A single-drug response prediction
does not establish combination synergy. Training Q-Former, a new GNN or a dynamic GRN is deferred
until a demonstrated agent task cannot be solved adequately with existing qualified tools.

## Repository finding and selected change

**Reproduced before editing:** `TaskInterpreter` stores constraints, endpoints, targets,
interventions, biological context and evidence gaps in `TaskIntent`. `ContextBuilder._packet`
rendered only the research question and supplied evidence as mandatory task state. Tool selection,
initial/repair planning and the initial Jev review consume `context.rendered`. Consequently,
information correctly extracted by the interpreter could disappear before a decision.

The saved reproduction supplies `Use existing public data only; no new wet-lab measurements.`,
an explicit viability endpoint and an unmeasured-target-engagement gap. None appears in the
pre-change context. Seven nonempty structured fields are absent. The defect is information loss;
it does not prove every earlier model call violated a constraint, because the research-question
text may sometimes repeat it.

**Selected optimization:** render the remaining structured task fields as mandatory context,
clearly labelled requested state rather than measured evidence. Retain explicit nulls, false,
empty lists, constraints and evidence gaps. Keep the existing research-question and supplied-
evidence sections. If the complete task state does not fit, return the existing explicit budget
error rather than dropping a constraint. Evidence cards remain atomic, with provenance and
limitations preserved when included.

This is a bounded agent-interface repair requiring no new neural module, provider or agent role.
It makes constraints visible; it does not introduce a deterministic interpreter/enforcer of
arbitrary natural-language constraints. Existing catalogue, premise and execution checks still
have their current scope. Long mandatory task state can leave less room for retrieved evidence.

Other observed opportunities remain **design**: compact tool execution history; model-visible
coverage/omission notices; a formal constraint schema; and independent held-out agent-policy
comparisons. Existing omitted-record IDs are audit metadata, not guaranteed model-visible text.
Lossy compression is deferred because removing a qualifier or provenance could change meaning.

## Acceptance protocol frozen before implementation

- Reproduce missing structured state on the old implementation with no network dependency.
- Verify all structured task fields survive to planner and tool-selection messages, including
  Unicode and unknown values. Verify the initial Jev review receives the same task constraints.
- Verify full-state overflow explicitly refuses instead of silently omitting constraints, while
  complete evidence cards still fit or are omitted atomically under a declared budget.
- Exercise rebuilding context after tool or visual feedback, so a repair round retains intent.
- Run relevant context, planner, tool and critic tests in the `maestro` Python environment;
  then run the complete test suite once the final change is stable.
- An optional live paired probe may use the same configured text model, catalogue, decoding
  settings and call/token caps, comparing legacy-rendered and repaired-rendered task state.
  Save actual prompts, answers, usage, latency and errors. This is an interface experiment:
  information content and input length differ; it is not equal-information or equal-token-use
  evidence for a better reasoning policy. Tiny disclosed-rule fixtures cannot establish
  biological utility, statistical significance or calibrated confidence. Deterministic prompt
  transport checks suffice to accept this repair without a successful API response.

## Execution record

**Implemented:** the selected mandatory task-state repair in `src/agent/context.py`.
Three new regressions first failed on the prior implementation and then passed. Existing
Jev/repair integration coverage now checks constraint and evidence-gap transport. The evidence
card fixture reserves 700 rather than 300 characters for the larger mandatory state while
retaining full-card and cap assertions. Validation in the maestro environment: **131 focused
tests and all 1,259 tests passed**.

The [paired probe](local_verification/task_state_probe.py) froze prompts before live calls and
replayed actual planner messages over two synthetic cases, each twice for the text endpoint.
The same catalogue offers existing archive review and a new independent assay; constraints
select the required route. No tool execution, scientific outcome or controller success is
measured. `deepseek-flash` selected the requested action 2/4 times with legacy rendering and
4/4 with full task state. Jev `jev-1.13.0` selected it 1/2 versus 2/2, with no recorded refusals.
Text token usage rose from 4,151 to 4,731 (about 14%). The model, catalogue, temperature (0) and
output cap (800 tokens) were held fixed; information content and realized tokens were not.

These are disclosed-constraint interface fixtures, not independent biological cases, calibrated
judgments or evidence of a better scientific policy. Full local prompts, answers, usage and
latency are in `outputs/task_state_probe_20260925/`; the reproduction command and remaining
research gates are in [task.md, section 10](../task.md#10-research-sequence-and-implementation-backlog),
with verified status in [section 11](../task.md#11-current-verified-status).
