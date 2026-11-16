# Audit factory

One runner for every Korbant audit. Each audit is a config file; each model family is a small adapter.

| File | What it does |
|---|---|
| `korbant_audit.py` | Sends the pre-registered BANKING77 and CLINC150 items to a model and records every answer. Resumable. Refuses scored runs until the config names a pre-registration commit. |
| `audits/<name>.json` | Pins the model, its exact revision, the packages and the pre-registration commit. |
| `kaggle_cell.py` | One cell for a free Kaggle GPU notebook: installs, downloads the pinned weights, runs everything, zips the results. |
| `score_all.py` | Scores every checkpoint with `jevcal` and prints the headline table plus selective risk. |

## Run an audit

1. Write the pre-registration and commit it.
2. Put that commit hash in `audits/<name>.json` as `prereg_commit` and commit again.
3. Paste `kaggle_cell.py` into a Kaggle notebook, set `AUDIT` and `REPO_COMMIT`, then Save and Run All.
4. Download `<name>-results.zip`, then `python score_all.py audits/<name>.json --jevcal ../jevcal`.

## Add a model

Write one function in `korbant_audit.py` that takes `(repo, revision, device)` and returns `ask(text, labels)` giving `choice`, `probabilities` and `confidence`. Register it in `ADAPTERS`. Nothing else changes, so every audit uses the same data, wording, record format and scorer.
