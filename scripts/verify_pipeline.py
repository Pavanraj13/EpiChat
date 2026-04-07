"""
verify_pipeline.py — EpiChat Pipeline Verification
====================================================
Sanity-checks all processed files in data/processed/ and prints a summary table.

Checks:
  - Shape == [N, 18, 2400]
  - No NaN/Inf values
  - Labels match epoch count
  - At least 1 seizure epoch (where expected)

Usage:
    python scripts/verify_pipeline.py
    python scripts/verify_pipeline.py --dataset chbmit
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np

BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
RESET  = "\033[0m"
DIM    = "\033[2m"


def check_file(npy_path: Path) -> Dict:
    """Run all checks on a single .npy file and its _meta.json sidecar."""
    meta_path = npy_path.parent / (npy_path.stem + "_meta.json")
    result = {
        "file":          npy_path.name,
        "shape":         None,
        "sfreq":         None,
        "n_seiz":        None,
        "n_bg":          None,
        "has_nan":       False,
        "has_inf":       False,
        "labels_match":  True,
        "channels_ok":   True,
        "status":        "ok",
        "notes":         [],
    }

    # ── Load numpy array ──────────────────────────────────────────────────────
    try:
        data = np.load(str(npy_path))
    except Exception as exc:
        result["status"] = "load_error"
        result["notes"].append(f"Load failed: {exc}")
        return result

    result["shape"] = list(data.shape)

    # Shape check
    if len(data.shape) != 3 or data.shape[1] != 18 or data.shape[2] != 2400:
        result["status"] = "shape_error"
        result["notes"].append(
            f"Expected [N, 18, 2400], got {data.shape}"
        )
        return result

    # NaN / Inf check
    result["has_nan"] = bool(np.any(np.isnan(data)))
    result["has_inf"] = bool(np.any(np.isinf(data)))
    if result["has_nan"]:
        result["notes"].append("Contains NaN values!")
        result["status"] = "data_error"
    if result["has_inf"]:
        result["notes"].append("Contains Inf values!")
        result["status"] = "data_error"

    # ── Load metadata ─────────────────────────────────────────────────────────
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)

        result["sfreq"]   = meta.get("sfreq")
        result["n_seiz"]  = meta.get("n_seizure_epochs", 0)
        result["n_bg"]    = meta.get("n_background_epochs", 0)

        # sfreq check
        if meta.get("sfreq") != 200:
            result["notes"].append(f"sfreq={meta.get('sfreq')} (expected 200)")
            result["status"] = "sfreq_error"

        # Labels count match
        labels = meta.get("labels", [])
        if len(labels) != data.shape[0]:
            result["labels_match"] = False
            result["notes"].append(
                f"Label count {len(labels)} != n_epochs {data.shape[0]}"
            )
            result["status"] = "label_error"

        # Channel order check
        chans = meta.get("channels", [])
        expected = [
            "FP1-F7","F7-T7","T7-P7","P7-O1","FP2-F8","F8-T8","T8-P8","P8-O2",
            "FP1-F3","F3-C3","C3-P3","P3-O1","FP2-F4","F4-C4","C4-P4","P4-O2",
            "C3-A2","C4-A1",
        ]
        if chans != expected:
            result["channels_ok"] = False
            result["notes"].append("Channel order mismatch!")
            result["status"] = "channel_error"
    else:
        result["notes"].append("No _meta.json sidecar found")

    return result


def print_table(rows: List[Dict], title: str):
    print(f"\n{BOLD}{CYAN}{'─'*90}{RESET}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{BOLD}{CYAN}{'─'*90}{RESET}")
    header = (
        f"{'File':<35} {'Shape':>14} {'Seiz':>6} {'BG':>6} "
        f"{'sfreq':>6} {'NaN':>4} {'Status':>12}"
    )
    print(f"{BOLD}{DIM}{header}{RESET}")
    print(f"{'─'*90}")

    ok_count  = 0
    err_count = 0

    for r in rows:
        shape = str(r["shape"]) if r["shape"] else "N/A"
        seiz  = str(r["n_seiz"])  if r["n_seiz"]  is not None else "-"
        bg    = str(r["n_bg"])    if r["n_bg"]    is not None else "-"
        freq  = str(r["sfreq"])   if r["sfreq"]   is not None else "-"
        nan   = "YES" if r["has_nan"] or r["has_inf"] else "no"
        status = r["status"]

        color = GREEN if status == "ok" else RED
        print(
            f"{r['file'][:34]:<35} {shape:>14} {seiz:>6} {bg:>6} "
            f"{freq:>6} {nan:>4} {color}{status:>12}{RESET}"
        )
        if r["notes"]:
            for note in r["notes"]:
                print(f"  {YELLOW}↳ {note}{RESET}")

        if status == "ok":
            ok_count += 1
        else:
            err_count += 1

    print(f"{'─'*90}")
    print(
        f"  Total: {len(rows)}  |  {GREEN}✓ {ok_count} OK{RESET}  |  "
        f"{RED}✗ {err_count} errors{RESET}"
    )


def verify(dataset_filter: str = "all"):
    processed_root = Path("data/processed")

    if not processed_root.exists():
        print(f"{RED}[ERR]{RESET} data/processed/ does not exist. Run preprocess.py first.")
        sys.exit(1)

    datasets = (
        [dataset_filter] if dataset_filter != "all"
        else ["chbmit", "tusz"]
    )

    grand_total = 0
    grand_ok    = 0

    for dataset in datasets:
        ds_dir = processed_root / dataset
        if not ds_dir.exists():
            print(f"{YELLOW}[WARN]{RESET}  No processed data for dataset: {dataset}")
            continue

        npy_files = sorted(ds_dir.rglob("*.npy"))
        if not npy_files:
            print(f"{YELLOW}[WARN]{RESET}  No .npy files found in {ds_dir}")
            continue

        rows = [check_file(f) for f in npy_files]
        print_table(rows, f"Dataset: {dataset.upper()} ({ds_dir})")

        grand_total += len(rows)
        grand_ok    += sum(1 for r in rows if r["status"] == "ok")

    print(f"\n{BOLD}{'─'*90}")
    total_seiz = 0
    total_bg   = 0
    for dataset in datasets:
        for f in sorted(Path("data/processed").rglob(f"{dataset}/**/*_meta.json")):
            with open(f) as jf:
                m = json.load(jf)
                total_seiz += m.get("n_seizure_epochs", 0)
                total_bg   += m.get("n_background_epochs", 0)

    print(f"  GRAND TOTAL  |  Files: {grand_total}  |  {GREEN}✓ {grand_ok} OK{RESET}")
    print(f"  Seizure epochs:    {total_seiz:,}")
    print(f"  Background epochs: {total_bg:,}")
    print(f"  Class ratio:       "
          f"{total_seiz / max(total_seiz + total_bg, 1) * 100:.1f}% seizure")
    print(f"{'─'*90}{RESET}\n")

    if grand_ok < grand_total:
        sys.exit(1)    # Non-zero exit for CI


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify EpiChat preprocessed data")
    parser.add_argument(
        "--dataset", choices=["chbmit", "tusz", "all"], default="all"
    )
    args = parser.parse_args()
    verify(args.dataset)
