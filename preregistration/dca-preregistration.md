# Differential Calibration Audit: re-checking confidence after a model update by labelling only what changed

**A pre-registered methods study (Korbant study M1)**

Bilal Jussab, Korbant (audit.korbant.co.uk)
Written 18 November 2026, before any of the quantities below have been computed.

## The question

A team sets a rule such as "act automatically when the model is at least 90% sure". Then the model is updated. The usual way to check that the rule is still safe is to label a fresh test set and audit again from scratch. This study asks whether almost all of that labelling can be skipped.

The idea: when the old and new versions give the same answer on an item, that answer is right for both or wrong for both. Labels already collected for the old version therefore carry over to the new one on every item where the two agree. New labels are needed only for items where the answer changed. On top of that, a simple bound shows, without any new labels, how far overconfidence can have moved.

## Prior work, and what is new here

- Balachandran (arXiv 2609.17560, July 2026) uses the same observation, that two models can only differ in risk where they disagree, to certify that an update did not make accuracy worse, labelling only sampled disagreements. Its guarantees cover losses that depend only on the predicted answer. The paper says the identity fails for "calibration losses on confidence scores", and it does not study selective risk at a confidence threshold, coverage, or calibration error. It is written for teams promoting their own models, not for an independent auditor.
- Work on negative flips (Yan et al. 2021; Träuble et al. 2021; Apple MUSCLE 2024) counts or reduces answers that change from right to wrong. It does not reuse labels to audit confidence.
- Label-free estimates of accuracy (agreement on the line, ATC) and of calibration under label shift (LaSCal, 2024) do not use a version pair.
- Shihab et al. (arXiv 2604.23987, 2026) show that conformal coverage can collapse before accuracy during continual fine-tuning.

What this study adds: the carry-over of labels applied to **confidence**. That means calibration, selective risk and coverage at fixed thresholds, a no-label bound on the change in overconfidence, and a paired test of calibration change. All of this is run as an independent, pre-registered audit on public version pairs. We claim only that we found no prior work doing this. A final search of arXiv and Semantic Scholar will be repeated before publication.

## Honest statement of what we already know

Korbant has already scored every version used here, one version at a time (Strands Decider 2B v19 and v2610; Mapika decider-2b v11 and v12). We therefore know each version's accuracy, calibration error and coverage, and we know that Mapika v12 is strongly underconfident while v11 is not. **None of the quantities in this study have been computed yet.** That covers the share of answers that changed, the bounds, the carry-over estimates, the paired tests, the monitor and the temperature fit. Because the version-level results are known, tests on these pairs are **retrospective**. The blind test is prospective: every new version pair that Korbant's weekly model watch finds after this commit will be run through this exact protocol before any per-version scoring.

## Data

The stored raw outputs from the audits, with per-item predicted label, full probability vector and gold label:

| Pair | Role | Banking77 items | CLINC150 out of scope items |
|---|---|---|---|
| Mapika v11 → v12 | Primary (known shipped temperature change) | 3,080 | 1,000 |
| Strands v19 → v2610 | Primary | 3,080 | 1,000 |
| Strands v2610 vs Mapika v11, Strands v2610 vs Mapika v12 | Secondary: different models, used to test the bound when many answers differ | 3,080 | 1,000 |

Files are listed by name and SHA-256 in `results/` and the freeze files of audits #2 and #3. Confidence is the probability of the chosen option, as in those audits. Correctness is an exact match with the dataset label. Hand-review corrections are not used in this study.

## Definitions

For versions A (old) and B (new) on the same n items:

- Disagreement rate d is the share of items where the top answers differ. No labels are needed.
- Overconfidence is mean confidence minus accuracy. Because accuracy can differ by at most d, the change in overconfidence lies in [Δconf − d, Δconf + d], where Δconf is the change in mean confidence. No new labels are needed.
- Coverage at threshold τ is the share of items with confidence ≥ τ, for τ in {0.80, 0.90, 0.95, 0.99}. No labels are needed.
- Carry-over audit of B: correctness of B is copied from A on agreeing items and taken from labels only on disagreeing items. Calibration error (10 equal-mass bins, as in our audits), Brier score and selective risk at each τ are then computed for B.
- Label saving is the number of labels used by the carry-over audit (the disagreeing items) divided by n.

## Hypotheses and pass marks (fixed now)

| # | Hypothesis | How it is judged |
|---|---|---|
| H1 | The bound contains the true change in overconfidence for every pair and dataset | Must hold in all cases. A failure means a code error, which we fix and report |
| H2 | The bound is narrow enough to use for version pairs of the same model | Reported as width 2d. Counted as useful when 2d ≤ 0.04. Prediction: useful for at least one of the two primary pairs on Banking77 |
| H3 | The carry-over audit reproduces the full-label calibration error, Brier score and selective risk of B exactly, while using only the disagreeing items' labels | Exact equality to 6 decimals (it is an identity; this checks the pipeline). Label saving reported per pair |
| H4 | Labelling only a random 25% of disagreeing items still gives selective risk within the Wilson 95% interval of the full-label value | Judged at each τ over 1,000 random draws (seed 20261118). Passes if at least 95% of draws fall inside |
| H5 | A paired test detects an injected confidence change with fewer items than an unpaired test | Simulation on Mapika v11 and Strands v19: temperature T in {1.1, 1.25, 1.5, 2.0} applied to the log probabilities; sample sizes n in {250, 500, 1,000, 3,080}; 1,000 draws each. Paired test: a one-sided t test on per-item Brier differences, α = 0.05. Unpaired test: a permutation test on the difference in calibration error, 1,000 permutations, α = 0.05. Prediction: the paired test has higher power at every T and n where neither is at 100% |
| H6 | A continuous monitor raises an alarm on the Mapika pair | Items are replayed in one fixed random order (seed 20261118). The e-process is a betting martingale on bounded per-item Brier differences (B minus A), with the bet size set by the running mean (the approximate GRAPA rule). Alarm when it reaches 20 (α = 0.05). Prediction: alarm on Mapika v11 → v12 on Banking77. For Strands, the result is reported with no prediction |
| H7 | The shipped temperature change can be recovered without labels and without reading the config | Fit a single T minimising mean KL divergence between B's probabilities and A's probabilities rescaled by T, over all Banking77 items. The configs give a ratio of 2.465 / 1.164 = 2.12. Prediction: the fitted ratio lies within ±15% of 2.12. The weights also differ between versions, so this is a test, not a certainty |

Results are reported whether they support the hypotheses or not.

## What could go wrong, fixed now

- If 2d > 0.10 for both primary pairs, the no-label bound is reported as too wide to be useful, and the study is written up as label carry-over only.
- Calls that failed in the original audits keep the treatment those audits gave them and are listed.
- Any change to this plan after commit is added as a dated, public amendment before the affected analysis is run.

## Code and publication

The analysis is a new script, `factory/dca.py`, written after this commit. It uses only numpy and scipy, reads the stored raw files, and does not call any model. No results from this study are published before the Strands results (on or after 30 November) and the Mapika results (on or after 2 December) are public and their right of reply windows have closed. The study is then published with its data, code and a DOI.
