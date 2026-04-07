import os
import urllib.request
import argparse
from pathlib import Path

BASE_URL = "https://physionet.org/files/chbmit/1.0.0"
OUTPUT_DIR = Path("C:/Users/U.PAVAN RAJ/Epichat_Data/raw/chbmit")
SUBJECTS = ["chb01", "chb03"]

def download_file(url: str, dest_path: Path):
    if dest_path.exists():
        print(f"[SKIP] Already exists: {dest_path.name}")
        return
    print(f"[DOWNLOADING] {url} -> {dest_path}")
    try:
        urllib.request.urlretrieve(url, str(dest_path))
    except Exception as e:
        print(f"[ERROR] Failed to download {url}: {e}")

def main(dry_run: bool):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Root metadata files
    metadata_files = ["RECORDS", "RECORDS-WITH-SEIZURES", "SUBJECT-INFO", "SHA256SUMS.txt"]
    for meta in metadata_files:
        dest = OUTPUT_DIR / meta
        url = f"{BASE_URL}/{meta}"
        if not dry_run:
            download_file(url, dest)
        else:
            print(f"[DRY RUN] Would download {url} to {dest}")

    # Read RECORDS to figure out all files, or we can just download RECORDS if not exists
    records_file = OUTPUT_DIR / "RECORDS"
    if not records_file.exists():
        print("[ERROR] RECORDS file not found. Metadata download must have failed.")
        return

    with open(records_file, 'r') as f:
        all_records = [line.strip() for line in f if line.strip()]

    # Filter files belonging to target subjects
    for record in all_records:
        # record looks like "chb01/chb01_01.edf"
        subject_dir = record.split('/')[0]
        if subject_dir in SUBJECTS:
            dest = OUTPUT_DIR / record
            dest.parent.mkdir(parents=True, exist_ok=True)
            url = f"{BASE_URL}/{record}"
            
            # CHB-MIT has an edf file and a .seizures file for some. But RECORDS only lists .edf
            # We should also download the summary text files if present: e.g. chb01/chb01-summary.txt
            if not dry_run:
                download_file(url, dest)
            else:
                print(f"[DRY RUN] Would download {url} to {dest}")
                
    # Also explicitly download the summary files for the subjects
    for subj in SUBJECTS:
        summary_name = f"{subj}/{subj}-summary.txt"
        summary_dest = OUTPUT_DIR / summary_name
        summary_url = f"{BASE_URL}/{summary_name}"
        if not dry_run:
            download_file(summary_url, summary_dest)
        else:
            print(f"[DRY RUN] Would download {summary_url} to {summary_dest}")
            
    print("\n[OK] CHB-MIT download script finished.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download CHB-MIT subset")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    
    main(args.dry_run)
