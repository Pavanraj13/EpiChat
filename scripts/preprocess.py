"""
preprocess.py — EEG Preprocessing Pipeline for EpiChat
=======================================================
Preprocesses CHB-MIT and TUSZ EDF files to:
  - 200 Hz sampling rate
  - BIOT 18-channel bipolar montage (exact channel order)
  - 12-second epochs (2400 samples @ 200 Hz)

Outputs per processed file:
  data/processed/<dataset>/<subject>/<stem>.npy      shape: [n_epochs, 18, 2400]
  data/processed/<dataset>/<subject>/<stem>_meta.json

Usage:
    python scripts/preprocess.py --dataset chbmit
    python scripts/preprocess.py --dataset tusz
    python scripts/preprocess.py --dataset all
    python scripts/preprocess.py --dataset chbmit --subject chb01 --dry-run
"""

import argparse
import json
import os
import re
import sys
import warnings
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

# Suppress MNE verbose output unless debug mode
warnings.filterwarnings("ignore", category=RuntimeWarning)
os.environ.setdefault("MNE_LOGGING_LEVEL", "ERROR")

try:
    import mne
    mne.set_log_level("ERROR")
except ImportError:
    print("[ERR] MNE not installed. Run: pip install mne")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════════════════════
# BIOT 18-CHANNEL SPECIFICATION
# (Yang et al., NeurIPS 2023 — "BIOT: Cross-data Biosignal Foundation Model")
# ═══════════════════════════════════════════════════════════════════════════════
BIOT_CHANNELS: List[str] = [
    "FP1-F7",   # 0
    "F7-T7",    # 1
    "T7-P7",    # 2
    "P7-O1",    # 3
    "FP2-F8",   # 4
    "F8-T8",    # 5
    "T8-P8",    # 6
    "P8-O2",    # 7
    "FP1-F3",   # 8
    "F3-C3",    # 9
    "C3-P3",    # 10
    "P3-O1",    # 11
    "FP2-F4",   # 12
    "F4-C4",    # 13
    "C4-P4",    # 14
    "P4-O2",    # 15
    "C3-A2",    # 16
    "C4-A1",    # 17
]

N_CHANNELS   = 18
TARGET_SFREQ = 200          # Hz
EPOCH_SEC    = 12           # seconds per epoch
EPOCH_SAMP   = TARGET_SFREQ * EPOCH_SEC   # 2400 samples

# ── CHB-MIT channel name aliases ──────────────────────────────────────────────
# CHB-MIT uses mixed formats; map common variants to BIOT names.
CHBMIT_ALIAS: Dict[str, str] = {
    # Common full names
    "FP1-F7": "FP1-F7", "F7-T7": "F7-T7", "T7-P7": "T7-P7", "P7-O1": "P7-O1",
    "FP2-F8": "FP2-F8", "F8-T8": "F8-T8", "T8-P8": "T8-P8", "P8-O2": "P8-O2",
    "FP1-F3": "FP1-F3", "F3-C3": "F3-C3", "C3-P3": "C3-P3", "P3-O1": "P3-O1",
    "FP2-F4": "FP2-F4", "F4-C4": "F4-C4", "C4-P4": "C4-P4", "P4-O2": "P4-O2",
    "C3-A2":  "C3-A2",  "C4-A1": "C4-A1",
    # Variants with dashes and spaces
    "FP1-F7-0": "FP1-F7", "F7-T7-0": "F7-T7", "T7-P7-0": "T7-P7",
    "P7-O1-0":  "P7-O1",  "FP2-F8-0": "FP2-F8", "F8-T8-0": "F8-T8",
    "T8-P8-0":  "T8-P8",  "P8-O2-0": "P8-O2",
    # Some CHB-MIT files use "T8-P8-0" suffix variants
    "T8-P8-0":  "T8-P8",
    # Old-style "T3"/"T4"/"T5"/"T6" → modern equivalents
    "FP1-T3": "FP1-F7",  "T3-T5":  "F7-T7",   "T5-O1":  "T7-P7",
    "FP2-T4": "FP2-F8",  "T4-T6":  "F8-T8",   "T6-O2":  "T8-P8",
}

# TUSZ uses a TCP (Temporal Central Parasagittal) bipolar montage
# Map common TUSZ channel names to BIOT equivalents
TUSZ_ALIAS: Dict[str, str] = {
    "EEG FP1-F7":   "FP1-F7",  "EEG F7-T3":   "F7-T7",  "EEG T3-T5":   "T7-P7",
    "EEG T5-O1":    "P7-O1",   "EEG FP2-F8":  "FP2-F8", "EEG F8-T4":   "F8-T8",
    "EEG T4-T6":    "T8-P8",   "EEG T6-O2":   "P8-O2",
    "EEG FP1-F3":   "FP1-F3",  "EEG F3-C3":   "F3-C3",  "EEG C3-P3":   "C3-P3",
    "EEG P3-O1":    "P3-O1",   "EEG FP2-F4":  "FP2-F4", "EEG F4-C4":   "F4-C4",
    "EEG C4-P4":    "C4-P4",   "EEG P4-O2":   "P4-O2",
    "EEG C3-A2":    "C3-A2",   "EEG C4-A1":   "C4-A1",
    # Without "EEG" prefix
    "FP1-F7": "FP1-F7",  "F7-T3": "F7-T7",  "T3-T5": "T7-P7",  "T5-O1": "P7-O1",
    "FP2-F8": "FP2-F8",  "F8-T4": "F8-T8",  "T4-T6": "T8-P8",  "T6-O2": "P8-O2",
    "FP1-F3": "FP1-F3",  "F3-C3": "F3-C3",  "C3-P3": "C3-P3",  "P3-O1": "P3-O1",
    "FP2-F4": "FP2-F4",  "F4-C4": "F4-C4",  "C4-P4": "C4-P4",  "P4-O2": "P4-O2",
    "C3-A2":  "C3-A2",   "C4-A1": "C4-A1",
}

# Colours
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def log(msg):  print(f"{CYAN}[INFO]{RESET}  {msg}")
def ok(msg):   print(f"{GREEN}[ OK ]{RESET}  {msg}")
def warn(msg): print(f"{YELLOW}[WARN]{RESET}  {msg}")
def err(msg):  print(f"{RED}[ERR ]{RESET}  {msg}", file=sys.stderr)


# ══════════════════════════════════════════════════════════════════════════════
# Seizure Label Parsing
# ══════════════════════════════════════════════════════════════════════════════

def parse_chbmit_summary(summary_path: Path) -> Dict[str, List[Tuple[float, float]]]:
    """
    Parse chbXX-summary.txt and return a dict mapping:
        edf_filename → [(seizure_start_sec, seizure_end_sec), ...]
    """
    seizure_map: Dict[str, List[Tuple[float, float]]] = {}
    if not summary_path.exists():
        warn(f"Summary not found: {summary_path}")
        return seizure_map

    current_file  = None
    starts: List[float] = []
    ends:   List[float] = []

    with open(summary_path, "r") as f:
        for line in f:
            line = line.strip()

            m = re.match(r"File Name:\s+(.+\.edf)", line, re.IGNORECASE)
            if m:
                if current_file and starts:
                    seizure_map[current_file] = list(zip(starts, ends))
                current_file = m.group(1).strip()
                starts, ends = [], []
                continue

            m = re.match(r"Seizure(?:\s+\d+)?\s+Start Time:\s+(\d+)\s+seconds", line, re.IGNORECASE)
            if m:
                starts.append(float(m.group(1)))
                continue

            m = re.match(r"Seizure(?:\s+\d+)?\s+End Time:\s+(\d+)\s+seconds", line, re.IGNORECASE)
            if m:
                ends.append(float(m.group(1)))

    if current_file and starts:
        seizure_map[current_file] = list(zip(starts, ends))

    return seizure_map


def parse_tse(tse_path: Path) -> List[Tuple[float, float]]:
    """
    Parse a TUSZ .tse file and return a list of (start, end) seizure intervals.
    """
    intervals = []
    if not tse_path.exists():
        return intervals
    with open(tse_path, "r", errors="ignore") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) >= 3 and parts[2].lower() == "seiz":
                try:
                    intervals.append((float(parts[0]), float(parts[1])))
                except ValueError:
                    pass
    return intervals


def make_epoch_labels(
    n_epochs: int,
    total_duration_sec: float,
    seizure_intervals: List[Tuple[float, float]],
) -> List[int]:
    """
    Assign a binary label to each epoch:
        1 = seizure, 0 = background
    An epoch is labeled seizure if its time window overlaps any seizure interval.
    """
    labels = []
    for i in range(n_epochs):
        epoch_start = i * EPOCH_SEC
        epoch_end   = epoch_start + EPOCH_SEC
        is_seiz = any(
            s < epoch_end and e > epoch_start
            for (s, e) in seizure_intervals
        )
        labels.append(1 if is_seiz else 0)
    return labels


# ══════════════════════════════════════════════════════════════════════════════
# Channel Mapping
# ══════════════════════════════════════════════════════════════════════════════

def map_channels(raw: mne.io.BaseRaw, dataset: str) -> Optional[mne.io.BaseRaw]:
    """
    Renames and reorders raw channels to match BIOT 18-channel specification.
    If bipolar channels are missing but unipolar exist, calculates them.
    Returns None if fewer than 15 of 18 required channels can be mapped.
    """
    # 1. First try simple aliasing (handles pre-computed bipolar)
    alias = CHBMIT_ALIAS if dataset == "chbmit" else TUSZ_ALIAS
    rename = {}
    for ch in raw.ch_names:
        ch_clean = ch.strip()
        if ch_clean in alias:
            biot_name = alias[ch_clean]
            if biot_name != ch_clean:
                rename[ch_clean] = biot_name
    if rename:
        raw.rename_channels(rename)

    # 2. Check what's missing
    missing = [ch for ch in BIOT_CHANNELS if ch not in raw.ch_names]
    
    # 3. If there are missing channels, try to construct them from unipolar nodes
    if missing:
        # Standardize node names to make lookup easy
        node_rename = {}
        node_alias = {"T3": "T7", "T4": "T8", "T5": "P7", "T6": "P8"}
        for ch in raw.ch_names:
            clean = ch.upper().replace("EEG ", "").replace("-REF", "").replace("-LE", "").strip()
            clean = node_alias.get(clean, clean)
            node_rename[clean] = ch  # mapping standardized node back to actual raw channel name
        
        # Now for each missing bipolar channel e.g. "FP1-F7"
        for bp in missing:
            if "-" in bp:
                anode, cathode = bp.split("-")
                # Do we have both unipolar nodes?
                if anode in node_rename and cathode in node_rename:
                    try:
                        mne.set_bipolar_reference(
                            raw, 
                            anode = node_rename[anode], 
                            cathode = node_rename[cathode], 
                            ch_name = bp, 
                            drop_refs = False, 
                            copy = False,
                            verbose = False
                        )
                    except Exception as e:
                        warn(f"Failed to create bipolar channel {bp}: {e}")

    # Keep only the 18 BIOT channels that exist
    available = [ch for ch in BIOT_CHANNELS if ch in raw.ch_names]
    missing   = [ch for ch in BIOT_CHANNELS if ch not in raw.ch_names]

    if len(available) < 15:
        warn(f"  Only {len(available)}/18 BIOT channels found. Skipping.")
        warn(f"  Missing: {missing[:5]}{'...' if len(missing) > 5 else ''}")
        return None

    if missing:
        warn(f"  {len(missing)} channels missing, will zero-pad: {missing}")

    # Pick available channels and reorder
    raw.pick_channels(available, ordered=True)
    return raw


def zero_pad_to_18(data: np.ndarray, available: List[str]) -> np.ndarray:
    """
    Inserts zero-padded rows for missing BIOT channels, preserving exact order.
    Input:  data shape [len(available), n_samples]
    Output: data shape [18, n_samples]
    """
    n_samples = data.shape[1]
    out = np.zeros((N_CHANNELS, n_samples), dtype=data.dtype)
    for i, biot_ch in enumerate(BIOT_CHANNELS):
        if biot_ch in available:
            idx = available.index(biot_ch)
            out[i] = data[idx]
    return out


# ══════════════════════════════════════════════════════════════════════════════
# Core Processing
# ══════════════════════════════════════════════════════════════════════════════

def process_edf(
    edf_path: Path,
    out_dir: Path,
    dataset: str,
    seizure_intervals: List[Tuple[float, float]],
    dry_run: bool = False,
) -> Optional[Dict]:
    """
    Process a single EDF file:
      1. Load with MNE
      2. Map channels to BIOT 18-ch
      3. Resample to 200 Hz
      4. Epoch into 12s windows
      5. Save .npy + _meta.json

    Returns a summary dict or None on failure.
    """
    stem    = edf_path.stem
    npy_out = out_dir / f"{stem}.npy"
    meta_out = out_dir / f"{stem}_meta.json"

    if npy_out.exists() and not dry_run:
        warn(f"  [SKIP] Already processed: {npy_out.name}")
        return {"file": stem, "status": "skip_exists"}

    # ── Load ──────────────────────────────────────────────────────────────────
    try:
        raw = mne.io.read_raw_edf(str(edf_path), preload=True, verbose=False)
    except Exception as exc:
        err(f"  Failed to load {edf_path.name}: {exc}")
        return {"file": stem, "status": "load_error", "error": str(exc)}

    original_sfreq = raw.info["sfreq"]
    log(f"  Loaded: {edf_path.name} | sfreq={original_sfreq:.0f}Hz | "
        f"{len(raw.ch_names)} channels | {raw.times[-1]:.1f}s")

    # ── Channel mapping ───────────────────────────────────────────────────────
    raw = map_channels(raw, dataset)
    if raw is None:
        return {"file": stem, "status": "channel_error"}

    available_channels = list(raw.ch_names)

    # ── Resample ──────────────────────────────────────────────────────────────
    if abs(raw.info["sfreq"] - TARGET_SFREQ) > 0.5:
        log(f"  Resampling {raw.info['sfreq']:.0f}Hz → {TARGET_SFREQ}Hz …")
        raw.resample(TARGET_SFREQ, npad="auto")

    # ── Get data ──────────────────────────────────────────────────────────────
    data = raw.get_data()                       # [n_channels, n_samples]
    data = zero_pad_to_18(data, available_channels)   # [18, n_samples]

    # ── Epoch ─────────────────────────────────────────────────────────────────
    n_samples = data.shape[1]
    n_epochs  = n_samples // EPOCH_SAMP

    if n_epochs == 0:
        warn(f"  Recording too short for even 1 epoch ({n_samples} samples). Skipping.")
        return {"file": stem, "status": "too_short"}

    # Trim to whole number of epochs
    data = data[:, : n_epochs * EPOCH_SAMP]
    epochs = data.reshape(n_epochs, N_CHANNELS, EPOCH_SAMP)  # [N, 18, 2400]

    # ── Label ─────────────────────────────────────────────────────────────────
    total_sec = n_epochs * EPOCH_SEC
    labels = make_epoch_labels(n_epochs, total_sec, seizure_intervals)
    n_seiz = sum(labels)

    log(f"  Epochs: {n_epochs} total | {n_seiz} seizure | "
        f"{n_epochs - n_seiz} background | shape: {epochs.shape}")

    if dry_run:
        print(f"  [DRY] Would save: {npy_out}")
        return {
            "file": stem, "status": "dry_run",
            "shape": list(epochs.shape), "n_seiz": n_seiz,
        }

    # ── Save ──────────────────────────────────────────────────────────────────
    out_dir.mkdir(parents=True, exist_ok=True)
    np.save(str(npy_out), epochs.astype(np.float32))

    metadata = {
        "file":              stem,
        "dataset":           dataset,
        "shape":             list(epochs.shape),   # [n_epochs, 18, 2400]
        "n_epochs":          n_epochs,
        "n_seizure_epochs":  n_seiz,
        "n_background_epochs": n_epochs - n_seiz,
        "labels":            labels,
        "seizure_intervals_sec": seizure_intervals,
        "channels":          BIOT_CHANNELS,
        "available_channels": available_channels,
        "sfreq":             TARGET_SFREQ,
        "epoch_sec":         EPOCH_SEC,
        "original_sfreq":    original_sfreq,
        "source_file":       str(edf_path),
    }
    with open(meta_out, "w") as f:
        json.dump(metadata, f, indent=2)

    ok(f"  Saved: {npy_out.name} ({epochs.nbytes / 1e6:.1f} MB)")
    return {"file": stem, "status": "ok", "shape": list(epochs.shape), "n_seiz": n_seiz}


# ══════════════════════════════════════════════════════════════════════════════
# Dataset-level processors
# ══════════════════════════════════════════════════════════════════════════════

def process_chbmit(subject_filter: Optional[str], dry_run: bool):
    raw_root = Path("C:/Users/U.PAVAN RAJ/Epichat_Data/raw/chbmit")
    out_root = Path("C:/Users/U.PAVAN RAJ/Epichat_Data/processed/chbmit")

    subjects = (
        [raw_root / subject_filter] if subject_filter
        else sorted([d for d in raw_root.iterdir() if d.is_dir()])
    )

    results = []
    for subj_dir in subjects:
        subject = subj_dir.name
        log(f"\n{'═'*60}")
        log(f"Processing CHB-MIT subject: {subject}")
        log(f"{'═'*60}")

        # Load seizure summary
        summary_path = subj_dir / f"{subject}-summary.txt"
        seizure_map  = parse_chbmit_summary(summary_path)

        edf_files = sorted(subj_dir.glob("*.edf"))
        if not edf_files:
            warn(f"No EDF files found in {subj_dir}")
            continue

        log(f"Found {len(edf_files)} EDF files")
        out_dir = out_root / subject

        for edf in edf_files:
            intervals = seizure_map.get(edf.name, [])
            r = process_edf(edf, out_dir, "chbmit", intervals, dry_run)
            if r:
                results.append(r)

    return results


def process_tusz(subject_filter: Optional[str], dry_run: bool):
    raw_root = Path("C:/Users/U.PAVAN RAJ/Epichat_Data/raw/tusz")
    out_root = Path("C:/Users/U.PAVAN RAJ/Epichat_Data/processed/tusz")

    edf_files = sorted(raw_root.rglob("*.edf"))
    if subject_filter:
        edf_files = [f for f in edf_files if subject_filter in str(f)]

    if not edf_files:
        warn("No TUSZ EDF files found. Run scripts/ingest_tusz.py first.")
        return []

    log(f"\nFound {len(edf_files)} TUSZ EDF files")
    results = []

    for edf in edf_files:
        # Derive relative output path mirroring the raw structure
        try:
            rel = edf.relative_to(raw_root)
        except ValueError:
            rel = Path(edf.name)

        out_dir   = out_root / rel.parent
        tse_path  = edf.with_suffix(".tse")
        intervals = parse_tse(tse_path)

        log(f"\nFile: {edf.name} | seizures: {len(intervals)}")
        r = process_edf(edf, out_dir, "tusz", intervals, dry_run)
        if r:
            results.append(r)

    return results


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

def print_summary(results: List[Dict]):
    total  = len(results)
    ok_c   = sum(1 for r in results if r.get("status") == "ok")
    skip   = sum(1 for r in results if r.get("status") == "skip_exists")
    errors = sum(1 for r in results if "error" in r.get("status", ""))
    dry    = sum(1 for r in results if r.get("status") == "dry_run")

    print(f"\n{'═'*60}")
    print(f"{BOLD}{'Preprocessing Summary':^60}{RESET}")
    print(f"{'═'*60}")
    print(f"  Total files processed:  {total}")
    print(f"  ✓ Successfully saved:   {ok_c + dry}")
    print(f"  ⟳ Already existed:      {skip}")
    print(f"  ✗ Errors:               {errors}")

    total_seiz = sum(r.get("n_seiz", 0) for r in results if r.get("status") in ("ok", "dry_run"))
    print(f"\n  Total seizure epochs:   {total_seiz}")
    print(f"{'═'*60}")
    print(f"\n  Output: data/processed/")
    print(f"  FastAPI can now read these files for inference.\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EpiChat EEG Preprocessing Pipeline")
    parser.add_argument(
        "--dataset", choices=["chbmit", "tusz", "all"], default="all",
        help="Which dataset to preprocess"
    )
    parser.add_argument(
        "--subject", type=str, default=None,
        help="Process only this subject (e.g., chb01)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be done without saving files"
    )
    args = parser.parse_args()

    print(f"\n{BOLD}{CYAN}=== EpiChat EEG Preprocessing Pipeline ==={RESET}")
    print(f"  Dataset:  {args.dataset}")
    print(f"  Subject:  {args.subject or 'all'}")
    print(f"  Target:   {TARGET_SFREQ} Hz | {N_CHANNELS} channels | {EPOCH_SEC}s epochs")
    print(f"  Dry-run:  {args.dry_run}\n")

    results = []
    if args.dataset in ("chbmit", "all"):
        results += process_chbmit(args.subject, args.dry_run)
    if args.dataset in ("tusz", "all"):
        results += process_tusz(args.subject, args.dry_run)

    print_summary(results)
