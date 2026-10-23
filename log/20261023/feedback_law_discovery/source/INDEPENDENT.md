# Independent biological feedback-law discovery

## Decision and scope

**One concrete law examined; STOP_AS_NEW_MECHANISM / NONE qualified.** The law below is executable in algebra and gives a specific cross-duration functional correction, but reduces exactly to ordinary growth-rate recalibration under its stated assumptions. It must not be renamed as a new inherited updater. This conclusion follows new original 2026 methods, not the old CRISPR-strength, CDK, AML/ALL, attenuation, or washout-two-module routes.

The full objective and the previous functional_mechanism_frontier decision were read. No same-round peer reports were read before this seal. Three purposeful GETs retrieved metadata and two original articles. Request URLs, HTTP status, UTC, and SHA-256 are in REQUESTS.jsonl. No data matrix, biological fitting, protected label, or author-code execution occurred.

## Fresh primary evidence

1. **VUScope: a mathematical model for evaluating image-based drug response measurements and predicting long-term incubation outcomes**, DOI **10.1093/bioinformatics/btaf679**, PMC12904834, published 4 February 2026. Methods 2.2 obtains cell-by-cell image counts every three hours for 120 hours, measures initial count, and uses six untreated controls/plate. Methods 2.4 describes 18 HDAC inhibitors, four lines, six concentration levels over 0–10 μM. Methods 2.6 explicitly fits a six-parameter joint dose–time surface: control and high-dose asymptotes evolve logistically; dose midpoint log10(IC50) is constant in time. Results 3.2 fits first 72 hours and forecasts 120 hours; the article additionally compares ATP-based CTG at 72 and 120 hours. Its “measured GRIVUS” is calculated from the full-120-hour fitted surface, not a directly observed independent scalar measurement. The article authenticates code/example-data websites, GitHub, and Zenodo 10.5281/zenodo.17610533; these were not fetched. No claim of an independently prepared leakage-free task split is made.

2. **A Classifier for Patient-Derived Colorectal Tumoroid Drug Sensitivity Using Confocal Imaging and Growth Rate Inhibition Metrics**, DOI **10.1158/2767-9764.crc-25-0473**, PMC13012007. Original methods quantify projected tumoroid-covered area, fit conventional GR dose responses, and discuss substantial untreated growth-rate heterogeneity across 16 samples. This is area, not authenticated absolute live-cell number. Its raw-data statement is reasonable request; no author contact or asset hunt follows. Its growth-normalization mechanism is a direct prior-art opponent, not an untested new idea.

These sources establish a real scientific failure mode: changing untreated expansion and observation modality can alter apparent drug response without identifying a change in intracellular drug exposure. Neither ATP/count disagreement nor a horizontal response shift alone establishes actual drug engagement strength.

## One explicit update law: control-clock transport of net-growth error

Application: after receiving short-duration cell-count feedback, correct a model's longer-duration viable-count forecast without treating altered basal growth as changed drug potency.

For one drug/dose, let the old model forecast initial-normalized counts f(t)>0 and untreated control f0(t)>1. At feedback time s, actual counts are n(s)>0 and n0(s)>1. Define the old and observed relative net-growth clocks

q_old = log(f(s))/log(f0(s)),
q_obs = log(n(s))/log(n0(s)).

For future time t, apply the specific multiplicative update

f_new(t) = f(t) * exp[(q_obs − q_old) log(f0(t))].

This changes the entire forecast trajectory, not merely an input feature. The inherited object would be the rule mapping short-time count/control discrepancies to the future multiplicative correction. Under exponential growth with stationary drug-relative net growth and a correctly predicted control, it exactly replaces the old drug-relative rate with the observed one. It is not the prior Norman global residual attenuation law and it does not use unknown target-time responses as inputs.

However, q is exactly the growth-normalized log-count quantity underlying conventional GR = 2^q − 1. The operation is therefore ordinary rate recalibration expressed multiplicatively. Re-estimating q from the same feedback in an exponential growth model produces the identical f_new trajectory under these assumptions. An implementation or biological win cannot prove an independent algorithmic contribution over that exact comparator. Ordinary components would be acceptable in a truly distinct rule; here the whole specified operation has the exact ordinary explanation.

## Small counterexamples and nonidentifiability

Constructed arithmetic, not cell experiments:

* **Growth-clock nuisance successfully cancelled.** Old control doubles in s and old treated count grows by sqrt(2), so q_old=1/2. A new context's control quadruples and treated count doubles, giving q_obs=1/2 again. A naive untreated-normalized viability changes from 1/sqrt(2) to 1/2 despite unchanged relative growth inhibition. The proposed update makes no drug-law change, exactly as ordinary GR correction does.
* **Assay calibration can fake a mechanistic update.** If the true treated count is doubled by an ATP-per-cell effect while untreated count is unaffected, q_obs shifts although proliferation/death need not change. Applying this law to ATP directly would corrupt future count predictions. Count-to-ATP calibration cannot be inferred from the outcome discrepancy alone. Source VUScope's cross-modality correlation is not an equality or absolute calibration certificate.
* **One early snapshot cannot determine later killing.** Two systems can have identical positive counts and control at s; one maintains its net growth and one begins delayed death immediately after s. The law returns identical long-time corrections although later viable counts differ. Thus measured short-time feedback cannot identify drug intensity, selection, and downstream delayed response without additional observations/assumptions. VUScope itself is a necessary stronger dose–time opponent rather than evidence that the stationary rate law solves the problem.

## Legal feedback and fair falsification

Legal inputs are measured initial/short-time counts and untreated controls at the same time, with their actual assay costs and segmentation limitations. No target-time GRIVUS/full-surface fit, late CTG, unknown exposure, or missing selection-state information may enter the updater. Images, ATP, projected area, and absolute viable count must not silently share a label definition. Control growth near zero makes the log ratio unstable; switching to another model on those exposed outcomes would be a different, separately specified rule, not a free repair.

The smallest honest comparison, if this ordinary adaptation were benchmarked, would start from identical long-time predictions, reveal a fixed short-time observation set, and compare future raw-count error and dose-selection regret. Opponents must include exact exponential/GR recalibration (which is algebraically identical here), VUScope's ordinary joint refit, a strong history/dose-time direct predictor with the same feedback, continual/replay adaptation, active feedback selection, simple mixtures, and equal-budget program search. Independent line/drug tasks, repeated observation costs, and no access to full-time fitted targets are required. World-model, agent, and inheritance effects need separate tests; none is implied by q reuse.

Success as a useful ordinary baseline would mean improved future functional prediction over frozen forecasts. Success as a new mechanism would additionally require a specified non-equivalent operation and measurable gain over exact rate recalibration and strong direct/joint refit. The present candidate fails that novelty condition before a biological fit. Stop immediately rather than add a learned gate, hidden exposure variable, delayed-death component, or new feedback menu merely to rescue this rule.

## Next action

**NONE qualified for a new functional-law experiment from this independent review.** Preserve this precise ordinary comparator and the short-feedback nonidentifiability counterexample. They narrow the next candidate requirement: it must specify what extra legal evidence makes a *different update operation* justified, not merely claim that observation discrepancy means action strength changed. No additional GET, data acquisition, author contact, fitting, or stopped-route restart is proposed.
