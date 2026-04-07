"""
ingest_tusz.py — TUSZ v1.5.2 Ingestion with Seizure-Only Filter
================================================================
Usage:
    python scripts/ingest_tusz.py --source "G:\\TUH_EEG_SEIZURE_v2" --dry-run
    python scripts/ingest_tusz.py --source "G:\\TUH_EEG_SEIZURE_v2"

The Drive folder (TUH_EEG_SEIZURE_v2) should be accessible as a local path
(i.e., downloaded or mounted via Google Drive for Desktop).

Rules:
  - Files ≤ 100 MB: always copied.
  - Files > 100 MB: copied ONLY if the paired .tse annotation file contains
    at least one 'seiz' label (seizure segment).

Output: data/raw/tusz/<patient>/<session>/<filename>
"""

import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Optional

# ── Configuration ──────────────────────────────────────────────────────────────
SIZE_LIMIT_MB   = 100
SIZE_LIMIT_BYTES = SIZE_LIMIT_MB * 1024 * 1024
OUTPUT_ROOT     = Path("C:/Users/U.PAVAN RAJ/Epichat_Data/raw/tusz")
SEIZURE_LABEL   = "seiz"   # TUSZ .tse label for seizures

# ── Colours ────────────────────────────────────────────────────────────────────
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
RESET  = "\033[0m"

def log(msg):  print(f"{CYAN}[INFO]{RESET}  {msg}")
def ok(msg):   print(f"{GREEN}[ OK ]{RESET}  {msg}")
def warn(msg): print(f"{YELLOW}[WARN]{RESET}  {msg}")
def err(msg):  print(f"{RED}[ERR ]{RESET}  {msg}", file=sys.stderr)


# ── TSE parser ─────────────────────────────────────────────────────────────────
def tse_has_seizure(tse_path: Path) -> bool:
    """
    Returns True if a .tse file contains at least one 'seiz' annotation.

    TUSZ .tse format:
        version = tse_v1.0.0
        <start_time> <stop_time> <label> <confidence>
        e.g.:
        0.0000 60.0000 bckg 1.0000
        60.0000 90.5000 seiz 1.0000
    """
    if not tse_path.exists():
        return False
    with open(tse_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("version"):
                continue
            parts = line.split()
            # Format: start stop label [confidence]
            if len(parts) >= 3 and parts[2].lower() == SEIZURE_LABEL:
                return True
    return False


def lbl_has_seizure(lbl_path: Path) -> bool:
    """
    Fallback: check channel-level .lbl annotation file for seizure labels.
    TUSZ .lbl format varies by version but 'seiz' appears in label fields.
    """
    if not lbl_path.exists():
        return False
    with open(lbl_path, "r", encoding="utf-8", errors="ignore") as f:
        return SEIZURE_LABEL in f.read().lower()


def file_is_seizure(edf_path: Path) -> bool:
    """
    Check if the EDF file has a paired annotation file that contains a seizure.
    Checks .tse first, then .lbl as fallback.
    """
    tse = edf_path.with_suffix(".tse")
    lbl = edf_path.with_suffix(".lbl")

    if tse.exists():
        return tse_has_seizure(tse)
    elif lbl.exists():
        return lbl_has_seizure(lbl)
    else:
        # No annotation file → treat conservatively (no seizure confirmed)
        warn(f"No annotation file for {edf_path.name} — will apply size limit strictly")
        return False


# ── Ingestion logic ────────────────────────────────────────────────────────────
def ingest(source_root: Path, dry_run: bool = False):
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    stats = {
        "scanned":         0,
        "copied":          0,
        "skipped_size":    0,
        "skipped_missing": 0,
        "already_exists":  0,
        "total_bytes":     0,
    }

    log(f"Scanning: {source_root}")
    log(f"Output:   {OUTPUT_ROOT}")
    log(f"Size threshold: {SIZE_LIMIT_MB} MB")
    if dry_run:
        warn("[DRY-RUN — no files will be copied]")

    # Walk the entire source tree for .edf files
    edf_files = sorted(source_root.rglob("*.edf"))
    if not edf_files:
        err(f"No .edf files found in: {source_root}")
        err("Check that the Drive folder is mounted / downloaded to that path.")
        sys.exit(1)

    log(f"Found {len(edf_files)} EDF files total")
    print()

    for edf in edf_files:
        stats["scanned"] += 1
        file_size = edf.stat().st_size
        size_mb   = file_size / (1024 * 1024)

        # Relative path for output mirroring (strip source root prefix)
        try:
            rel_path = edf.relative_to(source_root)
        except ValueError:
            rel_path = Path(edf.name)

        dest = OUTPUT_ROOT / rel_path

        # ── Skip if already exists ─────────────────────────────────────────────
        if dest.exists():
            stats["already_exists"] += 1
            warn(f"[SKIP-EXISTS] {rel_path} ({size_mb:.1f} MB)")
            continue

        # ── Size filter ────────────────────────────────────────────────────────
        if file_size > SIZE_LIMIT_BYTES:
            is_seiz = file_is_seizure(edf)
            if not is_seiz:
                stats["skipped_size"] += 1
                warn(f"[SKIP-SIZE]   {rel_path} ({size_mb:.1f} MB — no seizure annotation)")
                continue
            else:
                reason = f"seizure confirmed ({size_mb:.1f} MB)"
        else:
            reason = f"{size_mb:.1f} MB (under limit)"

        # ── Copy file + paired annotation files ───────────────────────────────
        if dry_run:
            print(f"  [DRY] COPY {rel_path} [{reason}]")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(edf, dest)
            ok(f"[COPY] {rel_path} [{reason}]")

            # Copy paired .tse / .lbl annotation files alongside EDF
            for ext in (".tse", ".lbl", ".tse_bi", ".lbl_bi"):
                annot = edf.with_suffix(ext)
                if annot.exists():
                    shutil.copy2(annot, dest.with_suffix(ext))

        stats["copied"]      += 1
        stats["total_bytes"] += file_size

    # ── Summary ────────────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print(f"{'TUSZ Ingestion Summary':^60}")
    print("=" * 60)
    print(f"  Total EDF files scanned:      {stats['scanned']}")
    print(f"  Copied:                       {stats['copied']}")
    print(f"  Already existed (skipped):    {stats['already_exists']}")
    print(f"  Skipped (>100MB, no seizure): {stats['skipped_size']}")
    print(f"  Total data ingested:          {stats['total_bytes'] / (1024**3):.2f} GB")
    print("=" * 60)

    if not dry_run:
        print(f"\n  Output saved to: {OUTPUT_ROOT.resolve()}")
        print("  Next: python scripts/preprocess.py --dataset tusz")


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest TUSZ v1.5.2 EDF files from a local Drive path into data/raw/tusz/"
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Path to the mounted/downloaded TUH_EEG_SEIZURE_v2 folder "
             '(e.g., "G:\\TUH_EEG_SEIZURE_v2" or "/mnt/g/TUH_EEG_SEIZURE_v2")',
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be copied without actually copying",
    )
    parser.add_argument(
        "--size-limit",
        type=int,
        default=SIZE_LIMIT_MB,
        help=f"Size limit in MB for non-seizure files (default: {SIZE_LIMIT_MB} MB)",
    )
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        err(f"Source path does not exist: {source}")
        err("Mount your Google Drive via 'Google Drive for Desktop' and re-run.")
        sys.exit(1)

    # Override global if provided
    SIZE_LIMIT_MB    = args.size_limit
    SIZE_LIMIT_BYTES = SIZE_LIMIT_MB * 1024 * 1024

    ingest(source_root=source, dry_run=args.dry_run)
