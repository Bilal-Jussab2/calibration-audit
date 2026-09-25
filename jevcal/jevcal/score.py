"""Score a responses file against the pre-registered rules.

Input: JSONL, one object per item:
  {"id", "gold", "pred", "probs": {label: p}, "confidence_score": float|null, "error": str|null}
Output: report.json, reliability_<signal>.png, summary.md in --out.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from . import metrics as M

SIGNALS = {
    "chosen_prob": "Probability on the chosen option",
    "confidence_score": "Separate confidence score",
}


def load_responses(path: Path) -> list[dict]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate ids in responses")
    return rows


def signal_values(rows: list[dict], signal: str) -> list[float] | None:
    if signal == "chosen_prob":
        return [float(r["probs"].get(r["pred"], 0.0)) for r in rows]
    vals = [r.get("confidence_score") for r in rows]
    return None if any(v is None for v in vals) else [float(v) for v in vals]


def score_in_scope(rows: list[dict]) -> dict:
    ok_rows = [r for r in rows if not r.get("error")]
    failures = [r["id"] for r in rows if r.get("error")]
    correct = [r["pred"] == r["gold"] for r in ok_rows]  # exact string match, nothing else
    out = {
        "n_items": len(rows),
        "n_scored": len(ok_rows),
        "failed_ids": failures,
        "accuracy": sum(correct) / len(correct),
        "accuracy_ci": M.wilson(sum(correct), len(correct)),
        "brier": M.brier([r["probs"] for r in ok_rows], [r["gold"] for r in ok_rows]),
        "signals": {},
    }
    for sig in SIGNALS:
        conf = signal_values(ok_rows, sig)
        if conf is None:
            continue
        bins = M.equal_mass_bins(conf, correct)
        pm = M.pass_mark(bins)
        wrong_hi, n_hi = M.confident_wrong_rate(conf, correct)
        out["signals"][sig] = {
            "bins": [M.as_dict(b) for b in bins],
            "ece": pm.ece,
            "mce": M.mce(bins),
            "pass_mark": M.as_dict(pm),
            "verdict": M.verdict(pm, None),
            "confident_wrong": {"wrong": wrong_hi, "of": n_hi, "rate": (wrong_hi / n_hi) if n_hi else None},
            "review_ids": [r["id"] for r, c, ok in zip(ok_rows, conf, correct) if c >= M.CONF_WRONG_THRESHOLD and not ok],
        }
    return out


def score_out_of_scope(rows: list[dict]) -> dict:
    ok_rows = [r for r in rows if not r.get("error")]
    out = {"n_items": len(rows), "n_scored": len(ok_rows), "failed_ids": [r["id"] for r in rows if r.get("error")], "signals": {}}
    for sig in SIGNALS:
        conf = signal_values(ok_rows, sig)
        if conf is None:
            continue
        s = sorted(conf)
        q = lambda p: s[min(len(s) - 1, int(p * len(s)))]
        n_hi = sum(c >= M.CONF_WRONG_THRESHOLD for c in conf)
        out["signals"][sig] = {"mean": sum(conf) / len(conf), "median": q(0.5), "p90": q(0.9),
                               "at_or_above_0.90": n_hi, "share_at_or_above_0.90": n_hi / len(conf)}
    return out


def plot_reliability(sig_report: dict, title: str, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    bins = sig_report["bins"]
    x = [b["mean_conf"] for b in bins]
    y = [b["accuracy"] for b in bins]
    err = [[b["accuracy"] - b["ci_low"] for b in bins], [b["ci_high"] - b["accuracy"] for b in bins]]
    lo = min(min(x), min(b["ci_low"] for b in bins), 0.0)
    fig, ax = plt.subplots(figsize=(5.2, 5.2), dpi=150)
    ax.plot([lo, 1], [lo, 1], color="#999999", lw=1, ls="--", label="perfect calibration")
    ax.errorbar(x, y, yerr=err, fmt="o-", color="#0C7160", ms=5, capsize=3, lw=1.5, label="observed (95% Wilson)")
    ax.set_xlim(lo, 1.01); ax.set_ylim(lo, 1.01)
    ax.set_xlabel("Mean confidence in group"); ax.set_ylabel("Share correct in group")
    ax.set_title(f"{title}\nECE {sig_report['ece']:.3f} · 10 equal-size groups", fontsize=9, wrap=True)
    ax.grid(alpha=0.25); ax.legend(loc="upper left", fontsize=8, frameon=False)
    fig.tight_layout(); fig.savefig(path); plt.close(fig)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--in-scope", type=Path, required=True)
    ap.add_argument("--out-of-scope", type=Path)
    ap.add_argument("--label", required=True, help="system name for titles")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args(argv)
    a.out.mkdir(parents=True, exist_ok=True)

    report = {"system": a.label, "in_scope": score_in_scope(load_responses(a.in_scope))}
    if a.out_of_scope:
        report["out_of_scope"] = score_out_of_scope(load_responses(a.out_of_scope))
    for sig, rep in report["in_scope"]["signals"].items():
        plot_reliability(rep, f"{a.label}\n{SIGNALS[sig]}", a.out / f"reliability_{sig}.png")
    (a.out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report["in_scope"].items() if k != "signals"}, default=str))
    for sig, rep in report["in_scope"]["signals"].items():
        print(sig, "ECE", round(rep["ece"], 4), "MCE", round(rep["mce"], 4), rep["pass_mark"], rep["confident_wrong"])
    if "out_of_scope" in report:
        print("OOS", report["out_of_scope"]["signals"])


if __name__ == "__main__":
    main()
