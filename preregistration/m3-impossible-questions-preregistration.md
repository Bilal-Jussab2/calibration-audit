# How sure are AI decision models on questions with no right answer?

**A pre-registered descriptive note (Korbant study M3)**

Bilal Jussab, Korbant (audit.korbant.co.uk)
Written 22 November 2026, before the combined table below is computed.

## The question

A team sets a rule such as "act automatically when the model is at least 90% sure". Real traffic contains questions that none of the allowed answers fit. This note measures how often five versions of three public decision models are confident on exactly those questions, and what that means for an automatic rule.

## Honest statement of what we already know

Each audit already reported the share of the 1,000 out of scope questions answered at 0.90 or above: Jev 14.9% (audit #1), Strands Decider 2B v19 11.3% and v2610 7.8%, Mapika decider-2b v11 11.2% and v12 0.2%. **The other thresholds, the intervals and the mixed-traffic figures below have not been computed.**

## Data

- CLINC150 out of scope test split, 1,000 questions, none of which fits any of the 150 allowed answers. Every answer is therefore wrong.
- BANKING77 test split (3,080 items) for the in-scope comparison.
- Stored raw outputs of the five versions, as in the audits. Confidence = probability of the chosen option.

## Measures (fixed now)

For each version:

1. Share of out of scope questions answered at 0.80, 0.90, 0.95 and 0.99 or above, each with a Wilson 95% interval. Mean and median confidence.
2. In-scope coverage and wrong rate at the same thresholds on BANKING77 (already in the audits, repeated for the table).
3. **Mixed traffic.** If a share p of traffic is out of scope, the share of automatic actions (confidence ≥ τ) that are wrong is
   (p × OOS share at τ + (1 − p) × in-scope coverage at τ × in-scope wrong rate at τ) ÷ (p × OOS share at τ + (1 − p) × in-scope coverage at τ),
   reported for p = 5% and 10%, τ = 0.90 and 0.95. The two test sets come from different sources (CLINC150 and BANKING77), so this is an illustration of the arithmetic, not a forecast for any real deployment, and is labelled as such.

No hypotheses are tested. The note is descriptive.

## What could go wrong, fixed now

- Both datasets are public and may be in the models' training data; Mapika's documentation lists the CLINC150 train split as a training source. The report says so.
- Any change to this plan after commit is added as a dated, public amendment first.

## Code and publication

A new script, `factory/oos_m3.py`, written after this commit. Nothing is published before the Strands results (on or after 30 November) and the Mapika results (on or after 2 December).
