"""Open baseline: TF-IDF + logistic regression trained on each dataset's own train split.

Writes responses in the harness format so the identical scorer runs on it and on Jev.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline, make_union

from jevcal.data import load_banking77, load_clinc


def build_model(seed: int):
    features = make_union(
        TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1),
        TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True, min_df=2),
    )
    return make_pipeline(features, LogisticRegression(C=10.0, max_iter=2000, random_state=seed))


def responses(model, items) -> list[dict]:
    proba = model.predict_proba([it.text for it in items])
    classes = list(model.classes_)
    out = []
    for it, p in zip(items, proba):
        probs = {c: float(v) for c, v in zip(classes, p)}
        pred = max(probs, key=probs.get)
        out.append({"id": it.id, "gold": it.gold, "pred": pred, "probs": probs, "confidence_score": None, "error": None})
    return out


def write_jsonl(rows: list[dict], path: Path) -> None:
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--out", type=Path, default=Path("results/baseline"))
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    train, _ = load_banking77(a.data, "train")
    test, _ = load_banking77(a.data, "test")
    m = build_model(a.seed).fit([t.text for t in train], [t.gold for t in train])
    write_jsonl(responses(m, test), a.out / "banking77_responses.jsonl")

    clinc = load_clinc(a.data)
    m2 = build_model(a.seed).fit([t.text for t in clinc["train"]], [t.gold for t in clinc["train"]])
    write_jsonl(responses(m2, clinc["oos_test"]), a.out / "clinc_oos_responses.jsonl")
    print("wrote", a.out)


if __name__ == "__main__":
    main()
