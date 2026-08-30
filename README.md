# Calibration audits for document AI

Independent measurement of whether a document-extraction system's confidence scores mean what they say — whether the fields it scores 0.9 are correct about 90% of the time.

Most extraction products route low-confidence fields to a human reviewer. That routing is only as good as the score doing it. Confidence scores are shipped almost universally and validated almost never.

**Worked example, on synthetic data:** https://bilal-jussab2.github.io/calibration-audit/

## What an engagement measures

- Expected and maximum calibration error, across ten confidence bands
- Wilson score intervals, so an overclaim is only reported where it exceeds sampling noise
- Brier score
- Risk-coverage analysis: the lowest review threshold meeting a stated accuracy target at the lower bound, not the point estimate
- The confident-and-wrong set: every automated decision above the threshold that was wrong
- Per-field and per-document-type breakdowns, because the aggregate hides the finding

Standard methods only. No proprietary metric, no model retraining, and every figure reproducible from the same inputs.

## Terms

200 extractions from your own test set. No customer data. Five working days. £450.

This is a measurement, not a certification. It is not an assurance engagement under ISAE 3000 or any equivalent standard, and no accreditation is claimed or implied.

---

Bilal Jussab · Calibration audits for document AI
