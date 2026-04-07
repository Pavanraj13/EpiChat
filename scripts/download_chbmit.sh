#!/usr/bin/env bash
# =============================================================================
# download_chbmit.sh — Download CHB-MIT subjects 01 and 03 from PhysioNet
# =============================================================================
# Usage (from WSL or Linux):
#   chmod +x scripts/download_chbmit.sh
#   bash scripts/download_chbmit.sh
#
# CHB-MIT is Open Access (no login required).
# Total download for chb01 + chb03: ~6-8 GB
# =============================================================================

set -euo pipefail

BASE_URL="https://physionet.org/files/chbmit/1.0.0"
OUTPUT_DIR="data/raw/chbmit"
SUBJECTS=("chb01" "chb03")
DRY_RUN=${DRY_RUN:-0}

mkdir -p "$OUTPUT_DIR"

log()  { echo -e "\033[36m[INFO]\033[0m  $*"; }
ok()   { echo -e "\033[32m[ OK ]\033[0m  $*"; }
warn() { echo -e "\033[33m[WARN]\033[0m  $*"; }
err()  { echo -e "\033[31m[ERR ]\033[0m  $*"; }

log "=== CHB-MIT Download Script ==="
log "Output dir: $OUTPUT_DIR"
[[ $DRY_RUN -eq 1 ]] && warn "[DRY-RUN MODE — no files will be downloaded]"

# ── Root metadata files ────────────────────────────────────────────────────────
log "Downloading root metadata..."
for meta in RECORDS RECORDS-WITH-SEIZURES SUBJECT-INFO SHA256SUMS.txt; do
    dest="$OUTPUT_DIR/$meta"
    if [[ -f "$dest" ]]; then
        warn "Already exists: $dest"
        continue
    fi
    if [[ $DRY_RUN -eq 0 ]]; then
        wget -q -c -O "$dest" "$BASE_URL/$meta" && ok "$meta" || err "Failed: $meta"
    else
        echo "  [DRY] wget -q -c -O $dest $BASE_URL/$meta"
    fi
done

# ── Per-subject download ───────────────────────────────────────────────────────
for subject in "${SUBJECTS[@]}"; do
    log "Subject: $subject"
    mkdir -p "$OUTPUT_DIR/$subject"

    if [[ $DRY_RUN -eq 0 ]]; then
        # wget recursive, only include this subject's directory
        # -r  : recursive
        # -N  : timestamps (skip if up-to-date)
        # -c  : continue partial downloads
        # -np : no parent
        # --cut-dirs=3 : strip 3 path levels (physionet.org/files/chbmit/1.0.0/)
        # -P  : output directory
        wget -r -N -c -np \
             --cut-dirs=4 \
             --include-directories="/$subject/" \
             --reject "index.html*" \
             -P "$OUTPUT_DIR" \
             "$BASE_URL/$subject/" \
        && ok "$subject download complete" \
        || err "$subject download failed — check network"
    else
        echo "  [DRY] wget -r -N -c -np --cut-dirs=4 -P $OUTPUT_DIR $BASE_URL/$subject/"
    fi
done

ok "All downloads complete!"
echo ""
echo "Files saved to: $OUTPUT_DIR"
echo "Next: python scripts/preprocess.py --dataset chbmit"
