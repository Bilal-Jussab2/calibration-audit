# Does Mapika decider's confidence mean what it says?

**A pre-registered test of a calibration claim (Korbant audit #3)**

Bilal Jussab, Korbant (audit.korbant.co.uk)
Written 16 November 2026, before any of the test data below has been sent to either checkpoint.

## Why this test

Mapika's decider is an open source family of decision models (Apache 2.0) that return a probability for every option instead of writing text. The model card for decider-2b is titled "typed decisions with calibrated probabilities in one forward pass". The project's own history file reports, for an earlier version (v6) with every label offered at once, accuracy 0.862 and calibration error 0.020 on Banking77, and accuracy 0.879 and calibration error 0.058 on CLINC. The current card reports a benchmark weighted calibration error of 0.164 on a sample of its Decision Index suite and says that figure is inflated by small samples. All of these are the maker's own measurements. This test measures the claim independently, with the same public data, wording, scorer and pass mark Korbant used for Jev (commit `6f429a5`) and Strands Decider (commit `f9ec718`).

## What is tested

Two checkpoints of Mapika/decider-2b on Hugging Face, reported as **two separate results, never combined**:

| Label | Revision | Pinned commit |
|---|---|---|
| v12 (current, branch main on 16 Nov 2026) | main | `7614a6c7ea5a047aa7d7bcfb1a0015469381c3e3` |
| v11 (previous release) | tag v11 | `998c591fe4efe2938fba456f94fc9884541700ec` |

The commit message for main reads "decider-2b v12"; the `decider_config.json` at that commit still carries the version string "2b-v11". The pinned commit, not the label, defines what is tested. Base model: Qwen/Qwen3.5-2B-Base. Inference package: decider-ai 1.10.0 from PyPI, exact library versions in the freeze file published with the results. Each checkpoint runs with the temperatures shipped in its own `decider_config.json`; nothing is tuned by us. Runs happen on a Kaggle notebook with an NVIDIA T4 GPU. Weights are downloaded once at the pinned commits, then scoring runs with the Hugging Face hub set offline. Kaggle's preinstalled torchao package is uninstalled first, as in audit #2; it plays no part in inference.

## The data

Identical to the Jev and Strands tests, fixed by checksum.

| Dataset | Role | Items | Licence | SHA-256 |
|---|---|---|---|---|
| BANKING77, test split | Main test | 3,080 | CC BY 4.0 | `d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d` |
| CLINC150, out of scope test set | Second test | 1,000 | CC BY 3.0 | `36923c3705a59e08fe9c3883d8bc2dd966ef93e22cb78ac41171782a698d56e0` |

## How the model is asked

Each utterance is sent on its own through the documented call `Decider.decide(context, questions)` with one question. The question text is the same instruction used for Jev and Strands, word for word: "Which of these customer service intents does the message express?" The options are the dataset's intent labels with underscores replaced by spaces, in alphabetical order. No answer is withheld: the abstention setting stays at its default of zero. The code is `factory/korbant_audit.py` with the `mapika` adapter. Before this document is committed only made up inputs are sent, to check loading and timing. A call that errors is recorded as a failure and listed, never dropped.

## What counts as correct

Exact match with the dataset's label. Nothing else.

## What is measured

The probability on the chosen option, judged as in the earlier audits: ten equal size groups (ties kept in dataset order), Wilson 95% intervals, expected calibration error, the largest gap, Brier score, a reliability diagram, and the share of answers at 0.90 or above that are wrong. For this model the separate confidence field returned by `decide` is the same number as the chosen option's probability, so there is one signal, not two.

Reported, not part of the pass mark: selective risk at fixed thresholds (0.80, 0.90, 0.95, 0.99), meaning the share of traffic at or above each threshold and the error rate within it, with Wilson intervals.

## The pass mark

Unchanged. The claim is **supported** on this test if all three hold:

1. Expected calibration error is 0.05 or lower.
2. No group's whole 95% interval sits more than 5 points below its average confidence.
3. The most confident group's accuracy interval lies entirely above the least confident group's.

## Label errors

Headline figures always use the original labels. Every answer at 0.90 or above that is marked wrong is reviewed by hand and sorted as a model error, a label error, or genuinely ambiguous. Items already reviewed in the Jev or Strands audits keep their verdict, because the verdict is about the item's label, not the model; items not seen before are reviewed fresh. The verdict table is unchanged:

| Original labels | Corrected labels | Verdict |
|---|---|---|
| Passes | Passes | Supported |
| Fails | Passes | Inconclusive, because the failure comes from label errors |
| Fails | Fails | Not supported on this test |

## The second test

The 1,000 CLINC150 out of scope utterances, offered only the 150 in scope intents. Reported, not scored.

## Limits

This model has seen data from both sources during training, and the maker says so: the Banking77 training half is listed among the v11 training sets, and the CLINC150 train split is listed in the v12 training mix. The test items here come from the BANKING77 test split and the CLINC150 out of scope test set, which the maker does not list as training data, but the model knows these label sets. The project states that its temperature was fitted without Banking77 and CLINC out of scope data. A pass therefore shows calibration on a task the model was partly trained for, which is a weaker result than a pass on unseen tasks, and the report will say so. One task, one language. Results apply to these two pinned commits only.

## Right of reply

Mapika receives the results at least 14 days before publication, through a GitHub issue on Mapika/decider, with an offer to publish their response in full.

## Changes after this is committed

Any change is added below with a date and reason. Nothing above is edited in place.

**Amendment 1 (16 November 2026, before any test data was sent).** The model is loaded with `use_graphs=False`, the library's eager path. Reason: a timing check with made up inputs showed that the default path compiles the model once per input shape with `torch.compile`, and on the Kaggle T4 machine one compile had not finished after six minutes, so a full run would not complete. The eager path is a documented option of `Decider`, it is the path the maker's own `decider.evaluate` uses, and the project's changelog reports that it reproduces the maker's research readout exactly, while the compiled path differs from it slightly (mean difference 0.0035 in probability). Nothing else changes: same checkpoints, data, wording, shipped temperatures, measures and pass mark.
