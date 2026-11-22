# Checking the BANKING77 test labels: which confident "mistakes" are really label errors

**A pre-registered methods note (Korbant study M2)**

Bilal Jussab, Korbant (audit.korbant.co.uk)
Written 22 November 2026, before the combined figures below are computed.

## The question

BANKING77 is a standard test set for banking intent classification. Ying and Thomas (2022) estimated that about 14% of its training examples may be mislabelled. As far as we know, nobody has published a check of the test split. A wrong test label turns a correct, confident answer into an apparent confident mistake, so it makes models look worse calibrated than they are.

Across our three audits we have checked by hand every test item that a model answered wrong at 90% confidence or above. This note pools those checks into one public list and measures how much the label errors change each model's figures.

## Honest statement of what we already know

- 201 test items have already been checked by hand: 156 in the Jev audit, 42 new in the Strands audit and 3 new in the Mapika audit (the rest of those audits reused earlier checks).
- The per-audit counts of label errors, model errors and ambiguous items are known (Jev 53 / 8 / 95; Strands new items 3 / 15 / 24; Mapika new items 1 / 2 / 0).
- The headline figures of each audit on the original labels are known. **The pooled list, the corrected-label figures for Strands and Mapika, and the lower bound on the test-split error rate below have not been computed.**

## Data

- BANKING77 test split, 3,080 items, original labels untouched.
- Stored raw outputs of five model versions: Jev (audit #1), Strands Decider 2B v19 and v2610 (audit #2), Mapika decider-2b v11 and v12 (audit #3). Files listed by name and SHA-256 in each audit's freeze file.

## Method (fixed now)

1. **Scope.** Every test item that at least one of the five versions answered wrong at confidence 0.90 or above (confidence = probability of the chosen option, as in the audits).
2. **Complete the checks.** Items in scope that have not been checked yet are checked in the same way: verdict model error, label error or ambiguous, with a one-line reason. For every label error we record the label a careful reader would choose. For every ambiguous item we record the set of fair labels (the original label plus any equally fair alternative).
3. **Second reviewer.** Most checks were proposed by an AI reviewer (Claude) and spot-checked by Bilal. A random 20 items (seed 20261122) are shown to Bilal blind: question text and the labels in play, without the first verdict. Agreement is reported as a share with a Wilson 95% interval. Disagreements are settled by discussion and both views are listed.
4. **Outputs.**
   - The full list: id, question, original label, verdict, proposed label or fair set, reason.
   - Label errors as a share of the 3,080 test items, with a Wilson 95% interval. **This is a lower bound**, because only confidently wrong items are checked.
   - For each of the five versions, on original and on corrected labels: accuracy, calibration error (10 equal-mass bins), the three-condition pass mark, and the share wrong at 0.90 or above. Corrected labels: a label error is replaced by the proposed label; on an ambiguous item any fair label counts as correct.
5. The original-label figures stay the headline everywhere. Corrected figures sit beside them, never in place of them.

## What could go wrong, fixed now

- Checks are a judgement. The list, the reasons and the blind agreement figure are published so anyone can disagree item by item.
- The scope is items the models got confidently wrong, so the list says nothing about label errors on items every model got right or answered with low confidence.
- Any change to this plan after commit is added as a dated, public amendment before the affected analysis is run.

## Code and publication

A new script, `factory/labels_m2.py`, written after this commit. Nothing from this note is published before the Strands results (on or after 30 November) and the Mapika results (on or after 2 December).
