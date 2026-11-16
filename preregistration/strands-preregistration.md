# Does Strands Decider's confidence mean what it says?

**A pre-registered test of a calibration claim (Korbant audit #2)**

Bilal Jussab, Korbant (audit.korbant.co.uk)
Written 15 November 2026, before any of the test data below has been sent to either checkpoint.

## Why this test

On 1 October 2026 AWS's Strands Labs released Strands Decider 2B, an open source decision model (Apache 2.0) that returns a probability for each option instead of writing text. Its model cards say every answer carries a calibrated confidence. The cards report their own calibration error on the JevBench public set (231 tasks, 4,096 token window): 0.072 for the current reference checkpoint (Brier 0.280) and 0.050 for the launch checkpoint (Brier 0.348). Both cards also say the confidence bands should be measured on your own traffic before you trust a threshold. Those figures are self-reported on the maker's chosen benchmark. This test measures the claim independently, on the same public data and method Korbant used for Jev (pre-registered 22 September 2026, commit `6f429a5`).

## What is tested

Two checkpoints, reported as **two separate results, never combined**:

| Label | Hugging Face repo | Pinned commit |
|---|---|---|
| v2610 (current reference) | StrandsAgents/strands-decider-2B-qwen3.5-v1-2610 | `216d1ccb46a9e9b036eb9187b248db98480f77d4` |
| v19 (launch checkpoint) | StrandsAgents/strands-decider-2B-hobson-v19 | `bb282d786bc251fd4e3068de3ada9ddbb38127cd` |

Base model for both: Qwen/Qwen3.5-2B-Base, commit `b1485b2fa6dfa1287294f269f5fb618e03d52d7c`. Inference package: strands-decider 0.3.0 from PyPI, exact library versions in `strands-freeze.txt`. Runs happen on a Kaggle notebook with an NVIDIA T4 GPU. Model weights are downloaded once at the pinned commits, then scoring runs with the Hugging Face hub set offline. The device, Python version and platform are recorded in each run's metadata file. Kaggle's preinstalled torchao package (0.10.0) is uninstalled before loading, because it conflicts with peft; it plays no part in inference. Results do not depend on where the arithmetic runs beyond floating point noise; any CPU rerun is reported as such.

## The data

Identical to the Jev test, fixed by checksum.

| Dataset | Role | Items | Licence | SHA-256 |
|---|---|---|---|---|
| BANKING77, test split | Main test | 3,080 | CC BY 4.0 | `d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d` |
| CLINC150, out of scope test set | Second test | 1,000 | CC BY 3.0 | `36923c3705a59e08fe9c3883d8bc2dd966ef93e22cb78ac41171782a698d56e0` |

## How the model is asked

Each utterance is sent on its own as a `choice` question. The options are the dataset's intent labels exactly as spelled, each described by the label with underscores replaced by spaces. The instruction is the same one used for Jev, word for word: "Which of these customer service intents does the message express?" The code is `run_strands.py`, published with the results. Before this document is committed only made up inputs are sent, to check loading and timing. A call that errors is recorded as a failure and listed, never dropped.

## What counts as correct

Exact match with the dataset's label. Nothing else.

## What is measured

As for Jev: the probability on the chosen option (primary signal) and the model's separate confidence field, each judged by the same rule. Ten equal size groups (ties kept in dataset order), Wilson 95% intervals, expected calibration error, the largest gap, Brier score, a reliability diagram, and the share of answers at 0.90 or above that are wrong.

Added for this audit (reported, not part of the pass mark): selective risk at fixed thresholds (0.80, 0.90, 0.95, 1.00), meaning the share of traffic at or above each threshold and the error rate within it, with Wilson intervals.

## The pass mark

Unchanged from the Jev test. For the chosen option's probability, the claim is **supported** on this test if all three hold:

1. Expected calibration error is 0.05 or lower.
2. No group's whole 95% interval sits more than 5 points below its average confidence.
3. The most confident group's accuracy interval lies entirely above the least confident group's.

## Label errors

Headline figures always use the original labels. Every answer at 0.90 or above that is marked wrong is reviewed by hand and sorted as a model error, a label error, or genuinely ambiguous. Items already reviewed in the Jev audit keep their published verdict, because the verdict is about the item's label, not the model; items not seen before are reviewed fresh. The verdict table is unchanged:

| Original labels | Corrected labels | Verdict |
|---|---|---|
| Passes | Passes | Supported |
| Fails | Passes | Inconclusive, because the failure comes from label errors |
| Fails | Fails | Not supported on this test |

## The second test

The 1,000 CLINC150 out of scope utterances, offered only the 150 in scope intents. Reported, not scored.

## Limits

Both datasets are public and may be in the base model's training data. One task, one language. Results apply to these two pinned checkpoints only, not to later versions or to other Strands models.

## Right of reply

Strands Labs receives the results at least 14 days before publication, through a GitHub issue on strands-labs/strands-decider and by email, with an offer to publish their response in full.

## Changes after this is committed

Any change is added below with a date and reason. Nothing above is edited in place.

**Amendments:** none.
