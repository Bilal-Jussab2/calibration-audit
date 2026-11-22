"""Korbant audit factory: run the pre-registered BANKING77 / CLINC150 items through any confidence-scoring model.

One runner for every audit. A model is supported by a small adapter (load + ask); an audit is a JSON config that pins
the model, its revision and the pre-registration commit. Output records are identical to run_jev.py / run_strands.py,
so the jevcal scorer applies unchanged.

  python korbant_audit.py audits/mapika.json fetch                  # download + checksum the two datasets
  python korbant_audit.py audits/mapika.json dummy                  # made-up inputs: load + timing check (allowed before pre-registration)
  python korbant_audit.py audits/mapika.json banking77 [--ckpt K] [--limit N] [--seconds S]   # resumable
  python korbant_audit.py audits/mapika.json all                    # every checkpoint, both datasets

Scored modes refuse to run until the config's prereg_commit is set.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
SHA256 = {
    "test.csv": "d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d",
    "data_full.json": "36923c3705a59e08fe9c3883d8bc2dd966ef93e22cb78ac41171782a698d56e0",
}
INSTRUCTIONS = "Which of these customer service intents does the message express?"  # identical across audits
DATASETS = ("banking77", "clinc_oos")

Item = tuple[str, str, "str | None"]
Ask = Callable[[str, list[str]], dict]  # (text, labels) -> {"choice", "probabilities", "confidence"}


# ---------------------------------------------------------------- data

SOURCES = {  # public originals; the checksum below is what makes a download trustworthy
    "test.csv": "https://raw.githubusercontent.com/PolyAI-LDN/task-specific-datasets/master/banking_data/test.csv",
    "data_full.json": "https://raw.githubusercontent.com/clinc/oos-eval/master/data/data_full.json",
}


def fetch_data(data_dir: Path) -> None:
    """Download any missing dataset file from its public source, then verify every checksum."""
    import urllib.request
    data_dir.mkdir(parents=True, exist_ok=True)
    for name, url in SOURCES.items():
        p = data_dir / name
        if not p.exists():
            urllib.request.urlretrieve(url, p)
        verify(p)
    print("data ok:", ", ".join(SOURCES))


def verify(path: Path) -> None:
    if not path.exists():
        sys.exit(f"{path} missing. Run: python korbant_audit.py <config> fetch")
    if hashlib.sha256(path.read_bytes()).hexdigest() != SHA256[path.name]:
        sys.exit(f"{path.name}: checksum does not match the pre-registration. Refusing to run.")


def load_items(which: str, data_dir: Path) -> tuple[list[Item], list[str]]:
    if which == "banking77":
        p = data_dir / "test.csv"
        verify(p)
        rows = list(csv.DictReader(p.open(newline="", encoding="utf-8")))
        return ([(f"b77-test-{i:04d}", r["text"], r["category"]) for i, r in enumerate(rows)],
                sorted({r["category"] for r in rows}))
    if which == "clinc_oos":
        p = data_dir / "data_full.json"
        verify(p)
        raw = json.loads(p.read_text(encoding="utf-8"))
        labels = sorted({lab for _, lab in raw["train"]})
        return [(f"clinc-oos_test-{i:04d}", t, None) for i, (t, _) in enumerate(raw["oos_test"])], labels
    raise ValueError(which)


# ---------------------------------------------------------------- adapters

def _snapshot(repo: str, rev: str) -> str:
    from huggingface_hub import snapshot_download
    return str(snapshot_download(repo, revision=rev, local_files_only=os.environ.get("HF_HUB_OFFLINE") == "1"))


def _device() -> str:
    import torch
    return "cuda" if torch.cuda.is_available() else "cpu"


def adapter_strands(repo: str, rev: str, device: str) -> Ask:
    from strands_decider.infer import load_engine
    from strands_decider.schema import ChoiceQuestion
    engine = load_engine(_snapshot(repo, rev), device=device)

    def ask(text: str, labels: list[str]) -> dict:
        q = ChoiceQuestion(instructions=INSTRUCTIONS, criteria={l: l.replace("_", " ") for l in labels})
        a = engine.ask(text, {"intent": q}).answers["intent"]
        return {"choice": a.choice, "probabilities": a.probabilities, "confidence": a.confidence}
    return ask


def adapter_mapika(repo: str, rev: str, device: str) -> Ask:
    """Mapika decider, documented interface Decider.decide(context, [{question, options}]), shipped temperatures.

    use_graphs=False selects the library's eager path, the one the maker's own decider.evaluate uses. The default
    compiled path needs a torch.compile per input shape, which does not finish on a Kaggle T4 (pre-registration amendment 1).
    """
    from decider.infer import Decider
    d = Decider(_snapshot(repo, rev), device=device, use_graphs=False)

    def ask(text: str, labels: list[str]) -> dict:
        shown = [l.replace("_", " ") for l in labels]
        back = dict(zip(shown, labels))
        r = d.decide(text, [{"question": INSTRUCTIONS, "options": shown}])[0]
        probs = {back[o]: p for o, p in r["probs"].items()}
        choice = back.get(r["choice"]) if r["choice"] is not None else max(probs, key=probs.get)
        return {"choice": choice, "probabilities": probs, "confidence": r["confidence"]}
    return ask


def adapter_glide(repo: str, rev: str, device: str) -> Ask:
    """Fastino GLiDE, documented interface Glide.from_pretrained(...).decide(state, questions), shipped temperature.

    The glide package ships inside the model repo, so it is imported from the pinned snapshot. The T4 has no native
    bfloat16, so the weights are loaded in float32 (exact conversion); vision is off because only text is sent.
    """
    import torch
    snap = _snapshot(repo, rev)
    if snap not in sys.path:
        sys.path.insert(0, snap)
    from glide import Glide
    dtype = torch.bfloat16 if (device == "cuda" and torch.cuda.is_bf16_supported(including_emulation=False)) else torch.float32
    m = Glide.from_pretrained(snap, device=device, dtype=dtype, vision=False)

    def ask(text: str, labels: list[str]) -> dict:
        q = {"type": "choice", "instructions": INSTRUCTIONS, "criteria": {l: l.replace("_", " ") for l in labels}}
        a = m.decide(state=text, questions={"intent": q})["answers"]["intent"]
        return {"choice": a["choice"], "probabilities": a["probabilities"], "confidence": a["confidence"]}
    return ask


def adapter_fake(repo: str, rev: str, device: str) -> Ask:
    """Deterministic stand-in used by the self-test only."""
    def ask(text: str, labels: list[str]) -> dict:
        h = int(hashlib.md5(text.encode()).hexdigest(), 16)
        j = h % len(labels)
        top = 0.5 + (h % 50) / 100
        probs = {l: (top if i == j else (1 - top) / (len(labels) - 1)) for i, l in enumerate(labels)}
        return {"choice": labels[j], "probabilities": probs, "confidence": top}
    return ask


ADAPTERS: dict[str, Callable[[str, str, str], Ask]] = {
    "strands": adapter_strands, "mapika": adapter_mapika, "glide": adapter_glide, "fake": adapter_fake}


# ---------------------------------------------------------------- run

def read_done(out: Path) -> set[str]:
    """Ids already recorded. Rewrites the file atomically, dropping a torn last line."""
    if not out.exists():
        return set()
    good, ids = [], set()
    for line in out.read_text(encoding="utf-8").splitlines():
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if rec["id"] not in ids:
            ids.add(rec["id"])
            good.append(line)
    tmp = out.with_suffix(".tmp")
    tmp.write_text("".join(l + "\n" for l in good), encoding="utf-8")
    os.replace(tmp, out)
    return ids


def record(ask: Ask, item: Item, labels: list[str], device: str) -> dict:
    item_id, text, gold = item
    t0 = time.monotonic()
    try:
        a, err = ask(text, labels), None
        if a["choice"] not in (a["probabilities"] or {}):
            a, err = None, "chosen label missing from probabilities"
    except Exception as e:  # recorded, never dropped
        a, err = None, f"{type(e).__name__}: {e}"[:500]
    return {
        "id": item_id, "gold": gold, "status": 200 if a else 0,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pred": a["choice"] if a else None,
        "probs": a["probabilities"] if a else None,
        "confidence_score": a["confidence"] if a else None,
        "error": err, "seconds": round(time.monotonic() - t0, 3), "device": device,
    }


class Audit:
    def __init__(self, cfg_path: Path, data_dir: Path, out_dir: Path):
        self.cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
        for k in ("audit", "adapter", "checkpoints"):
            if k not in self.cfg:
                sys.exit(f"{cfg_path.name}: missing '{k}'")
        if self.cfg["adapter"] not in ADAPTERS:
            sys.exit(f"unknown adapter {self.cfg['adapter']!r}; known: {sorted(ADAPTERS)}")
        self.data_dir, self.out_dir = data_dir, out_dir
        self._loaded: dict[str, tuple[Ask, str]] = {}

    def checkpoint(self, ckpt: str | None) -> list[str]:
        cks = self.cfg["checkpoints"]
        if ckpt and ckpt not in cks:
            sys.exit(f"unknown checkpoint {ckpt!r}; known: {sorted(cks)}")
        return [ckpt] if ckpt else list(cks)

    def model(self, ckpt: str) -> tuple[Ask, str]:
        if ckpt not in self._loaded:
            repo, rev = self.cfg["checkpoints"][ckpt]
            device = _device() if self.cfg["adapter"] != "fake" else "cpu"
            t0 = time.monotonic()
            self._loaded = {ckpt: (ADAPTERS[self.cfg["adapter"]](repo, rev, device), device)}  # one model in memory
            print(f"loaded {repo}@{rev[:7]} on {device} in {time.monotonic() - t0:.0f}s")
        return self._loaded[ckpt]

    def run(self, which: str, ckpt: str, limit: int | None = None, seconds: float | None = None) -> int:
        if not self.cfg.get("prereg_commit"):
            sys.exit("prereg_commit is empty: commit the pre-registration first, then set it in the config.")
        items, labels = load_items(which, self.data_dir)
        name = self.cfg["audit"]
        out = self.out_dir / f"{name}_{ckpt}_{which}_raw.jsonl"
        self.out_dir.mkdir(parents=True, exist_ok=True)
        done = read_done(out)
        todo = [it for it in items if it[0] not in done][: limit or None]
        if not todo:
            print(f"{which} {ckpt}: already complete ({len(done)} of {len(items)})")
            return 0
        ask, device = self.model(ckpt)
        (self.out_dir / f"{name}_{ckpt}_run_meta.json").write_text(json.dumps({
            "audit": name, "adapter": self.cfg["adapter"], "checkpoint": self.cfg["checkpoints"][ckpt],
            "prereg_commit": self.cfg["prereg_commit"], "device": device,
            "python": platform.python_version(), "platform": platform.platform(),
        }, indent=1), encoding="utf-8")
        deadline = time.monotonic() + seconds if seconds else None
        n = 0
        with out.open("a", encoding="utf-8") as f:
            for it in todo:
                if deadline and time.monotonic() > deadline:
                    break
                f.write(json.dumps(record(ask, it, labels, device)) + "\n")
                f.flush()
                n += 1
                if n % 100 == 0:
                    print(f"  {which} {ckpt}: {len(done) + n} of {len(items)}")
        failed = sum(1 for l in out.read_text(encoding="utf-8").splitlines() if json.loads(l)["status"] != 200)
        print(f"{which} {ckpt}: {len(done) + n} of {len(items)} recorded, {failed} failed -> {out.name}")
        return failed

    def dummy(self, ckpt: str) -> None:
        ask, device = self.model(ckpt)
        labels = [f"made_up_option_{i:02d}" for i in range(77)]
        labels[3] = "weather_question"
        times = []
        for i in range(20):
            t0 = time.monotonic()
            a = ask(f"Is it going to rain tomorrow? ({i})", labels)
            times.append(time.monotonic() - t0)
        times.sort()
        med = times[len(times) // 2]
        print(f"{ckpt}: choice {a['choice']} | confidence {a['confidence']:.3f} | {len(a['probabilities'])} probabilities | "
              f"median {med:.2f}s/item on {device} -> about {med * 4080 / 3600:.1f} h for 4,080 items")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("config", type=Path)
    ap.add_argument("mode", choices=["fetch", "dummy", *DATASETS, "all"])
    ap.add_argument("--ckpt")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--seconds", type=float, help="stop after this many seconds (resume later)")
    ap.add_argument("--data", type=Path, default=HERE / "data")
    ap.add_argument("--out", type=Path, default=HERE / "results")
    a = ap.parse_args(argv)
    if a.mode == "fetch":
        return fetch_data(a.data)
    audit = Audit(a.config, a.data, a.out)
    for ck in audit.checkpoint(a.ckpt):
        if a.mode == "dummy":
            audit.dummy(ck)
        else:
            for ds in (DATASETS if a.mode == "all" else (a.mode,)):
                audit.run(ds, ck, a.limit, a.seconds)


if __name__ == "__main__":
    main()
