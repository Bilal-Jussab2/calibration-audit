"""Send the pre-registered test items to Jev and record every raw response.

Standard library only. The API key is read from .env or .env.txt beside this file
and is never printed, logged or written to any output.

  python run_jev.py dummy                 # made-up inputs: check the API and response shape
  python run_jev.py banking77 [--limit N] # resumable; appends to results/jev_banking77_raw.jsonl
  python run_jev.py clinc_oos [--limit N]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
API_URL = "https://api.typesafe.ai/v1/systemone"
MODEL = "jev-latest"
SHA256 = {
    "test.csv": "d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d",
    "data_full.json": "36923c3705a59e08fe9c3883d8bc2dd966ef93e22cb78ac41171782a698d56e0",
}
# Fixed before the first scored call (pre-registration section 3). Published verbatim.
INSTRUCTIONS = "Which of these customer service intents does the message express?"
RETRIES = 3
RETRY_STATUS = {429, 500, 502, 503, 504, 529}


def load_key() -> str:
    for name in (".env", ".env.txt"):
        p = HERE / name
        if p.exists():
            for line in p.read_text(encoding="utf-8-sig").splitlines():
                k, _, v = line.partition("=")
                if k.strip() == "TYPESAFE_API_KEY" and v.strip():
                    return v.strip().strip("'\"")
    sys.exit("No TYPESAFE_API_KEY found in .env or .env.txt")


def verify(path: Path) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != SHA256[path.name]:
        sys.exit(f"{path.name}: checksum does not match the pre-registration. Refusing to run.")


def build_request(text: str, labels: list[str]) -> dict:
    return {
        "state": text,
        "model": MODEL,
        "questions": {
            "intent": {
                "type": "choice",
                "instructions": INSTRUCTIONS,
                "criteria": {lab: lab.replace("_", " ") for lab in labels},
            }
        },
    }


def call(key: str, body: dict) -> tuple[int, dict | str]:
    data = json.dumps(body).encode("utf-8")
    last: tuple[int, dict | str] = (0, "no attempt")
    for attempt in range(RETRIES + 1):
        req = urllib.request.Request(API_URL, data=data, method="POST", headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last = (e.code, e.read().decode("utf-8", errors="replace")[:2000])
            if e.code not in RETRY_STATUS:
                return last
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            last = (0, f"network error: {type(e).__name__}")
        time.sleep(2 ** attempt)
    return last


def find_answer(resp) -> dict | None:
    """Locate the answer object for question 'intent' without assuming exact nesting."""
    if isinstance(resp, dict):
        if "probabilities" in resp and ("choice" in resp or "confidence" in resp):
            return resp
        if isinstance(resp.get("intent"), dict) and "probabilities" in resp["intent"]:
            return resp["intent"]
        for v in resp.values():
            hit = find_answer(v)
            if hit:
                return hit
    elif isinstance(resp, list):
        for v in resp:
            hit = find_answer(v)
            if hit:
                return hit
    return None


def load_items(which: str) -> tuple[list[tuple[str, str, str | None]], list[str]]:
    if which == "banking77":
        p = HERE / "data" / "test.csv"
        verify(p)
        rows = list(csv.DictReader(p.open(newline="", encoding="utf-8")))
        items = [(f"b77-test-{i:04d}", r["text"], r["category"]) for i, r in enumerate(rows)]
        return items, sorted({r["category"] for r in rows})
    p = HERE / "data" / "data_full.json"
    verify(p)
    raw = json.loads(p.read_text(encoding="utf-8"))
    labels = sorted({lab for _, lab in raw["train"]})
    items = [(f"clinc-oos_test-{i:04d}", t, None) for i, (t, _) in enumerate(raw["oos_test"])]
    return items, labels


def read_done(out: Path) -> set[str]:
    """Ids already recorded. A partial last line (from an interrupted write) is dropped."""
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
    out.write_text("".join(l + "\n" for l in good), encoding="utf-8")
    return ids


def record(item: tuple[str, str, str | None], key: str, labels: list[str]) -> dict:
    item_id, text, gold = item
    status, resp = call(key, build_request(text, labels))
    ans = find_answer(resp) if status == 200 else None
    return {
        "id": item_id, "gold": gold, "status": status,
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pred": ans.get("choice") if ans else None,
        "probs": ans.get("probabilities") if ans else None,
        "confidence_score": ans.get("confidence") if ans else None,
        "error": None if ans else (resp if isinstance(resp, str) else "answer not found in response"),
        "raw": resp,
    }


def run(which: str, limit: int | None, workers: int, seconds: float | None) -> None:
    key = load_key()
    items, labels = load_items(which)
    out = HERE / "results" / f"jev_{which}_raw.jsonl"
    out.parent.mkdir(exist_ok=True)
    done = read_done(out)
    todo = [it for it in items if it[0] not in done][: limit or None]
    deadline = time.monotonic() + seconds if seconds else None
    lock, written = threading.Lock(), 0
    with out.open("a", encoding="utf-8") as f, ThreadPoolExecutor(max_workers=workers) as pool:
        pending = iter(todo)
        futures = set()

        def submit_next() -> None:
            if deadline and time.monotonic() > deadline:
                return
            nxt = next(pending, None)
            if nxt:
                futures.add(pool.submit(record, nxt, key, labels))

        for _ in range(workers):
            submit_next()
        while futures:
            fut = next(as_completed(futures))
            futures.discard(fut)
            line = json.dumps(fut.result()) + "\n"
            with lock:
                f.write(line)
                f.flush()
                written += 1
            submit_next()
    print(f"{which}: {len(done) + written} of {len(items)} recorded -> {out.name}")


def dummy() -> None:
    key = load_key()
    labels = [f"made_up_option_{i:02d}" for i in range(77)]
    labels[3] = "weather_question"
    status, resp = call(key, build_request("Is it going to rain tomorrow?", labels))
    print("status:", status)
    ans = find_answer(resp) if status == 200 else None
    print("answer found:", bool(ans))
    if ans:
        print("choice:", ans.get("choice"), "| confidence:", ans.get("confidence"),
              "| n probabilities:", len(ans.get("probabilities") or {}))
    shape = json.dumps(resp, indent=1)[:1500] if isinstance(resp, dict) else str(resp)[:800]
    print("response (truncated):", shape)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["dummy", "banking77", "clinc_oos"])
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seconds", type=float, help="stop starting new calls after this many seconds")
    a = ap.parse_args()
    dummy() if a.mode == "dummy" else run(a.mode, a.limit, a.workers, a.seconds)
