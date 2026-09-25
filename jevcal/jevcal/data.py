"""Load the pre-registered datasets and refuse to run on anything else."""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

# Fixed in the pre-registration (commit 6f429a5, 22 Sep 2026). Never edit.
SHA256 = {
    "banking77_test": "d12d6e3bc4c3103966ae786dc435913c0c563dfa328f5a3646d0e62cfeeb474d",
    "clinc150_full": "36923c3705a59e08fe9c3883d8bc2dd966ef93e22cb78ac41171782a698d56e0",
}


@dataclass(frozen=True)
class Item:
    id: str
    text: str
    gold: str | None  # None for out-of-scope items (no correct option exists)


def _verify(path: Path, key: str) -> None:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != SHA256[key]:
        raise ValueError(f"{path.name}: checksum {digest} does not match pre-registered {SHA256[key]}")


def load_banking77(data_dir: Path, split: str = "test") -> tuple[list[Item], list[str]]:
    path = data_dir / f"{split}.csv"
    if split == "test":
        _verify(path, "banking77_test")
    with path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    items = [Item(f"b77-{split}-{i:04d}", r["text"], r["category"]) for i, r in enumerate(rows)]
    labels = sorted({r["category"] for r in rows})
    return items, labels


def load_clinc(data_dir: Path) -> dict[str, list[Item]]:
    path = data_dir / "data_full.json"
    _verify(path, "clinc150_full")
    raw = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, list[Item]] = {}
    for split, rows in raw.items():
        oos = split.startswith("oos")
        out[split] = [Item(f"clinc-{split}-{i:04d}", t, None if oos else lab) for i, (t, lab) in enumerate(rows)]
    return out
