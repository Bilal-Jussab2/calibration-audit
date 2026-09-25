# jevcal

The code behind [Does Jev's confidence mean what it says?](../preregistration/jev-preregistration.md), a pre-registered calibration test of TypeSafe AI's Jev.

It sends every test item to Jev, records every raw response, and scores whether Jev's confidence matches how often it is right. Anyone with a Jev API key can run it again and should get the same numbers.

## Run it

You need Python 3.10 or later.

```
pip install -r requirements.txt
python -m pytest -q tests
```

**1. Get the data.** Put these three files in a `data/` folder. The code checks each one against the SHA-256 in the pre-registration and refuses to run on anything else.

| File | Source |
|---|---|
| `test.csv`, `train.csv` | BANKING77, [PolyAI-LDN/task-specific-datasets](https://github.com/PolyAI-LDN/task-specific-datasets) |
| `data_full.json` | CLINC150, [clinc/oos-eval](https://github.com/clinc/oos-eval) |

**2. Add your key.** Create a file called `.env` next to `run_jev.py` containing one line: `TYPESAFE_API_KEY=your_key`. The key is never printed or written anywhere else, and `.gitignore` keeps it out of git.

**3. Run Jev.** Runs are resumable, so you can stop and restart at any point.

```
python run_jev.py dummy          # made up inputs, checks the API works
python run_jev.py banking77      # 3,080 calls
python run_jev.py clinc_oos      # 1,000 calls
```

**4. Score it.**

```
python -m jevcal.score --label "Jev" --out results/jev \
  --in-scope results/jev_banking77_raw.jsonl \
  --out-of-scope results/jev_clinc_oos_raw.jsonl
```

This writes `report.json` and a reliability diagram for each confidence signal.

## What is where

| Path | What it does |
|---|---|
| `run_jev.py` | The exact request sent to Jev. Standard library only |
| `jevcal/data.py` | Loads the datasets and enforces the checksums |
| `jevcal/metrics.py` | Equal size confidence groups, Wilson intervals, calibration error, Brier score, and the pre-registered pass mark |
| `jevcal/score.py` | Turns raw responses into the report |
| `baselines/tfidf_logreg.py` | A simple open model, used only to check the scoring code |
| `tests/` | 13 tests. The two data tests skip until the data is downloaded |

## Licence

MIT. See `LICENSE`.
