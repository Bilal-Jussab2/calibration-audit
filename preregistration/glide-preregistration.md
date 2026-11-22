# Does GLiDE's confidence mean what it says?

**A pre-registered test of a calibration claim (Korbant audit #4)**

Bilal Jussab, Korbant (audit.korbant.co.uk)
Written 22 November 2026, before any of the test data below has been sent to the model.

## Why this test

On 19 November 2026 Fastino published GLiDE, a family of decision models that return a probability for each option instead of writing text, in a paper titled "GLiDE: A Fast, Calibrated Decision Model Distilled from Reasoning Teachers" (arXiv 2611.26509). The paper reports an expected calibration error of 2.0% for its 27B base model and 2.1% for the released 27B model. The 2B model card gives no calibration figure of its own and says that probabilities are model estimates and that decision thresholds should be set on your own data. This test measures the 2B model independently, on the same public data and method Korbant used for Jev (commit `6f429a5`), Strands Decider (commit `f9ec718`) and Mapika decider (commit `8207f3e`).

## What is tested

One checkpoint:

| Label | Hugging Face repo | Pinned commit |
|---|---|---|
| 2b | fastino/GLiDE-2B | `742ba093a930f229c0e01622aa1c421dc9e2b70b` |

The paper's calibration figures are for the 27B model. This test is of the 2B model, so it checks whether the family's calibration claim holds for the smaller model the maker also ships, not the 27B figure itself.

Inference uses the `glide` package shipped inside the model repository at the pinned commit (`Glide.from_pretrained`, then `decide`), with the softmax temperature in its `decision_config.json` (1.0). Runs happen on a Kaggle notebook with an NVIDIA T4 GPU. The T4 has no native bfloat16 support, so the model is loaded in float32 (the published bfloat16 weights convert to float32 exactly). Exact library versions are recorded in a freeze file. Weights are downloaded once at the pinned commit, then scoring runs with the Hugging Face hub set offline. The device, Python version and platform are recorded in the run's metadata file.

Licence: Fastino Community License. Section 6(b) states that evaluation, testing, benchmarking and research are not Production use. The published report will carry the attribution "Built with Fastino GLiDE".

## The data

Identical to the earlier audits, fixed by checksum.

| Dataset | Role | Items | Licence | SHA-256 |
|---|---|---|---|---|
| BANKING77, test split | Main test | 3,080 | CC BY 4.0 | `d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d` |
| CLINC150, out of scope test set | Second test | 1,000 | CC BY 3.0 | `36923c3705a59e08fe9c3883d8bc2dd966ef93e22cb78ac41171782a698d56e0` |

## How the model is asked

Each utterance is sent on its own as a `choice` question. The options are the dataset's intent labels exactly as spelled, each described by the label with underscores replaced by spaces. The instruction is the same one used in every audit, word for word: "Which of these customer service intents does the message express?" The code is `factory/korbant_audit.py` (adapter `glide`) with the config `factory/audits/glide.json`. Before this document is committed only made up inputs are sent, to check loading and timing. A call that errors is recorded as a failure and listed, never dropped.

## What counts as correct

Exact match with the dataset's label. Nothing else.

## What is measured

As in every audit: the probability on the chosen option (primary signal) and the model's separate confidence field (for GLiDE, the top probability minus the second), each judged by the same rule. Ten equal size groups (ties kept in dataset order), Wilson 95% intervals, expected calibration error, the largest gap, Brier score, a reliability diagram, and the share of answers at 0.90 or above that are wrong. Selective risk at 0.80, 0.90, 0.95 and 0.99, with Wilson intervals (reported, not part of the pass mark).

Note: GLiDE's confidence field is a margin, not a probability, so judging it as a probability is expected to look worse. The verdict uses the chosen option's probability only.

## The pass mark

Unchanged from the earlier audits. For the chosen option's probability, the claim is **supported** on this test if all three hold:

1. Expected calibration error is 0.05 or lower.
2. No group's whole 95% interval sits more than 5 points below its average confidence.
3. The most confident group's accuracy interval lies entirely above the least confident group's.

## Label errors

Headline figures always use the original labels. Every answer at 0.90 or above that is marked wrong is reviewed by hand and sorted as a model error, a label error, or genuinely ambiguous. Items already reviewed in earlier audits keep their published verdict; items not seen before are reviewed fresh. The verdict table is unchanged:

| Original labels | Corrected labels | Verdict |
|---|---|---|
| Passes | Passes | Supported |
| Fails | Passes | Inconclusive, because the failure comes from label errors |
| Fails | Fails | Not supported on this test |

## The second test

The 1,000 CLINC150 out of scope utterances, offered only the 150 in scope intents. Reported, not scored.

## Limits

Both datasets are public and may be in the model's training data; the paper does not list its training data. One task, one language, one pinned checkpoint. Results do not apply to the 27B model, to the 0.8B model or to later versions.

## Right of reply

Fastino receives the results at least 14 days before publication, through a discussion on the model's Hugging Face page and by email, with an offer to publish their response in full.

## Changes after this is committed

Any change is added below with a date and reason. Nothing above is edited in place.

**Amendments:** none.
