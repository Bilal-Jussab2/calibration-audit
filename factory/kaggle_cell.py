# Korbant audit factory: paste this one cell into a Kaggle notebook (Accelerator: GPU T4, Internet: On), then Save & Run All.
# Change only the two lines below. REPO_COMMIT pins the runner and config; the config pins the model and the pre-registration.
AUDIT = "mapika"
REPO_COMMIT = "PASTE_COMMIT_HASH"

import json, os, subprocess, sys, urllib.request
W = "/kaggle/working"; os.chdir(W); os.makedirs("audits", exist_ok=True)
RAW = f"https://raw.githubusercontent.com/Bilal-Jussab2/calibration-audit/{REPO_COMMIT}/factory"
for f in ["korbant_audit.py", f"audits/{AUDIT}.json"]:
    urllib.request.urlretrieve(f"{RAW}/{f}", f)
cfg = json.load(open(f"audits/{AUDIT}.json"))
pip = [sys.executable, "-m", "pip"]
subprocess.run(pip + ["uninstall", "-y", "-q", "torchao"])            # Kaggle's copy conflicts with peft; not used in inference
subprocess.run(pip + ["install", "-q", *cfg.get("pip", [])], check=True)
from huggingface_hub import snapshot_download
for repo, rev in list(cfg["checkpoints"].values()) + cfg.get("extra_snapshots", []):
    print("downloaded", snapshot_download(repo, revision=rev))
subprocess.run(pip + ["freeze"], stdout=open(f"results-freeze-{AUDIT}.txt", "w"))
run = lambda *a: subprocess.run([sys.executable, "korbant_audit.py", f"audits/{AUDIT}.json", *a], check=True,
                                env={**os.environ, "HF_HUB_OFFLINE": "1"})
run("fetch"); run("dummy")
if cfg.get("prereg_commit"):
    run("all")                                                          # resumable: rerun the cell to continue
    subprocess.run(["zip", "-qr", f"{AUDIT}-results.zip", "results", f"results-freeze-{AUDIT}.txt"])
else:
    print("prereg_commit is empty: only the made-up timing check ran.")
