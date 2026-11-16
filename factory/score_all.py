"""Score every checkpoint of an audit with jevcal and print the headline table.

  python score_all.py audits/mapika.json --results results --jevcal ../jevcal
Writes results/<audit>_<ckpt>_report/ (report.json, reliability PNGs, summary.md) and selective-risk tables.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

THRESHOLDS = (0.80, 0.90, 0.95, 0.99)


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / d
    return max(0.0, c - h), min(1.0, c + h)


def selective(rows: list[dict]) -> list[dict]:
    ok = [(r["probs"][r["pred"]], r["pred"] == r["gold"]) for r in rows if r["status"] == 200]
    out = []
    for t in THRESHOLDS:
        sel = [o for c, o in ok if c >= t]
        w = len(sel) - sum(sel)
        lo, hi = wilson(w, len(sel))
        out.append({"threshold": t, "coverage": len(sel) / len(ok), "n": len(sel), "wrong": w,
                    "wrong_rate": w / len(sel) if sel else None, "ci": [lo, hi]})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("--results", type=Path, default=Path("results"))
    ap.add_argument("--jevcal", type=Path, required=True, help="folder that contains the jevcal package")
    a = ap.parse_args()
    cfg = json.loads(a.config.read_text())
    name = cfg["audit"]
    print(f"| checkpoint | failures | accuracy | ECE | MCE | pass mark | wrong at >=0.90 | OOS answered at >=0.90 |\n|---|---|---|---|---|---|---|---|")
    for ck in cfg["checkpoints"]:
        b77, oos = (a.results / f"{name}_{ck}_{d}_raw.jsonl" for d in ("banking77", "clinc_oos"))
        if not b77.exists():
            print(f"| {ck} | not run | | | | | | |")
            continue
        out = a.results / f"{name}_{ck}_report"
        cmd = [sys.executable, "-m", "jevcal.score", "--in-scope", str(b77.resolve()), "--label", f"{name} {ck}", "--out", str(out.resolve())]
        if oos.exists():
            cmd += ["--out-of-scope", str(oos.resolve())]
        subprocess.run(cmd, check=True, cwd=a.jevcal, stdout=subprocess.DEVNULL)
        rows = [json.loads(l) for l in b77.read_text().splitlines()]
        sr = selective(rows)
        (out / "selective_risk.json").write_text(json.dumps(sr, indent=1))
        rep = json.loads((out / "report.json").read_text())
        sig = rep["in_scope"]["signals"]["chosen_prob"]
        fails = sum(r["status"] != 200 for r in rows)
        s90 = sr[1]
        oos_rows = [json.loads(l) for l in oos.read_text().splitlines()] if oos.exists() else []
        oos90 = (sum(1 for r in oos_rows if r["status"] == 200 and r["probs"][r["pred"]] >= 0.9) / len(oos_rows)) if oos_rows else None
        acc = sum(r["status"] == 200 and r["pred"] == r["gold"] for r in rows) / len(rows)
        passed = sig["verdict"]
        print(f"| {ck} | {fails} | {acc:.1%} | {sig['ece']:.4f} | {sig['mce']:.3f} | {passed} | "
              f"{s90['wrong']}/{s90['n']} ({s90['wrong_rate']:.1%}) | {'' if oos90 is None else f'{oos90:.1%}'} |")


if __name__ == "__main__":
    main()
