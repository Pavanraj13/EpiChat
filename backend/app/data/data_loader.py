"""
data_loader.py — FastAPI data access utility for processed EEG files
=====================================================================
Provides functions to load preprocessed .npy + metadata for inference testing.

Usage in FastAPI routes:
    from app.data.data_loader import load_eeg_sample, list_available_files
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

PROCESSED_ROOT = Path("data/processed")

# BIOT 18-channel specification (must match preprocess.py)
BIOT_CHANNELS: List[str] = [
    "FP1-F7", "F7-T7", "T7-P7", "P7-O1",
    "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
    "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
    "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
    "C3-A2",  "C4-A1",
]


class EEGSample:
    """Wrapper for a loaded EEG numpy file + its metadata."""

    def __init__(self, data: np.ndarray, meta: Dict):
        self.data  = data          # shape: [n_epochs, 18, 2400]
        self.meta  = meta
        self.labels: List[int] = meta.get("labels", [])

    @property
    def n_epochs(self) -> int:
        return self.data.shape[0]

    @property
    def n_seizure_epochs(self) -> int:
        return int(np.sum(self.labels))

    @property
    def shape(self) -> Tuple[int, ...]:
        return tuple(self.data.shape)

    def get_epoch(self, idx: int) -> np.ndarray:
        """Return a single epoch as [18, 2400] float32 array."""
        if idx < 0 or idx >= self.n_epochs:
            raise IndexError(f"Epoch index {idx} out of range [0, {self.n_epochs})")
        return self.data[idx]

    def get_seizure_epochs(self) -> np.ndarray:
        """Return all seizure-labeled epochs. Shape: [n_seiz, 18, 2400]."""
        mask = np.array(self.labels) == 1
        return self.data[mask]

    def get_background_epochs(self) -> np.ndarray:
        """Return all background-labeled epochs. Shape: [n_bg, 18, 2400]."""
        mask = np.array(self.labels) == 0
        return self.data[mask]

    def to_inference_batch(self, epoch_idx: Optional[int] = None) -> np.ndarray:
        """
        Prepare data for model inference.
        Returns shape: [1, 18, 2400] (single epoch) or [N, 18, 2400] (all epochs).
        """
        if epoch_idx is not None:
            return self.get_epoch(epoch_idx)[np.newaxis, ...]   # [1, 18, 2400]
        return self.data                                         # [N, 18, 2400]

    def summary(self) -> Dict:
        return {
            "file":       self.meta.get("file"),
            "dataset":    self.meta.get("dataset"),
            "shape":      list(self.shape),
            "n_epochs":   self.n_epochs,
            "n_seizure":  self.n_seizure_epochs,
            "n_bg":       self.n_epochs - self.n_seizure_epochs,
            "sfreq":      self.meta.get("sfreq"),
            "epoch_sec":  self.meta.get("epoch_sec"),
            "channels":   BIOT_CHANNELS,
        }


def load_eeg_sample(
    dataset: str,
    subject: str,
    filename: str,
) -> EEGSample:
    """
    Load a preprocessed EEG file by dataset/subject/filename.

    Args:
        dataset:  'chbmit' or 'tusz'
        subject:  e.g. 'chb01' or TUSZ patient folder name
        filename: stem of the file (without .npy), e.g. 'chb01_01'

    Returns:
        EEGSample object with .data [n_epochs, 18, 2400] and .meta dict

    Raises:
        FileNotFoundError if the file doesn't exist
        ValueError if the shape is wrong
    """
    # Strip .npy extension if provided
    stem = filename.replace(".npy", "")

    npy_path  = PROCESSED_ROOT / dataset / subject / f"{stem}.npy"
    meta_path = PROCESSED_ROOT / dataset / subject / f"{stem}_meta.json"

    if not npy_path.exists():
        raise FileNotFoundError(
            f"Processed file not found: {npy_path}\n"
            f"Run scripts/preprocess.py --dataset {dataset} --subject {subject}"
        )

    data = np.load(str(npy_path)).astype(np.float32)

    if len(data.shape) != 3 or data.shape[1] != 18 or data.shape[2] != 2400:
        raise ValueError(
            f"Unexpected shape {data.shape} — expected [N, 18, 2400]"
        )

    meta: Dict = {}
    if meta_path.exists():
        with open(meta_path) as f:
            meta = json.load(f)

    return EEGSample(data=data, meta=meta)


def list_available_files(dataset: Optional[str] = None) -> List[Dict]:
    """
    List all available processed files in data/processed/.

    Returns a list of dicts with:
        { dataset, subject, file, n_epochs, n_seizure, shape }
    """
    files: List[Dict] = {}

    if dataset:
        search_roots = [PROCESSED_ROOT / dataset]
    else:
        search_roots = [d for d in PROCESSED_ROOT.iterdir() if d.is_dir()]

    results = []
    for root in search_roots:
        if not root.exists():
            continue
        ds_name = root.name
        for meta_path in sorted(root.rglob("*_meta.json")):
            with open(meta_path) as f:
                meta = json.load(f)
            results.append({
                "dataset":   ds_name,
                "subject":   meta_path.parent.name,
                "file":      meta.get("file"),
                "shape":     meta.get("shape"),
                "n_epochs":  meta.get("n_epochs"),
                "n_seizure": meta.get("n_seizure_epochs"),
                "n_bg":      meta.get("n_background_epochs"),
                "sfreq":     meta.get("sfreq"),
            })

    return results


def get_dataset_stats(dataset: Optional[str] = None) -> Dict:
    """Return aggregate stats across all processed files."""
    files = list_available_files(dataset)
    total_epochs = sum(f.get("n_epochs", 0) or 0 for f in files)
    total_seiz   = sum(f.get("n_seizure", 0) or 0 for f in files)
    return {
        "n_files":         len(files),
        "total_epochs":    total_epochs,
        "seizure_epochs":  total_seiz,
        "background_epochs": total_epochs - total_seiz,
        "seizure_ratio":   round(total_seiz / max(total_epochs, 1), 4),
        "datasets":        list({f["dataset"] for f in files}),
    }
