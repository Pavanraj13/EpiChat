"""
inference_data_routes.py — FastAPI routes for EEG data access
=============================================================
Add these routes to your FastAPI app to expose processed EEG data
for inference testing.

Mount with:
    from app.data.inference_data_routes import router as data_router
    app.include_router(data_router, prefix="/data", tags=["EEG Data"])
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import numpy as np

from app.data.data_loader import (
    load_eeg_sample,
    list_available_files,
    get_dataset_stats,
    BIOT_CHANNELS,
)

router = APIRouter()


@router.get("/files", summary="List all processed EEG files")
def list_files(dataset: Optional[str] = Query(None, description="Filter by dataset: chbmit or tusz")):
    """Returns a list of all available preprocessed EEG files."""
    files = list_available_files(dataset)
    return {"files": files, "total": len(files)}


@router.get("/stats", summary="Get dataset statistics")
def dataset_stats(dataset: Optional[str] = Query(None)):
    """Returns aggregate statistics across all preprocessed files."""
    return get_dataset_stats(dataset)


@router.get("/channels", summary="Get BIOT 18-channel order")
def get_channels():
    """Returns the BIOT 18-channel specification used for all processed files."""
    return {"channels": BIOT_CHANNELS, "n_channels": len(BIOT_CHANNELS)}


@router.get("/{dataset}/{subject}/{filename}/meta", summary="Get file metadata")
def get_file_meta(dataset: str, subject: str, filename: str):
    """Returns the metadata JSON sidecar for a processed EEG file."""
    try:
        sample = load_eeg_sample(dataset, subject, filename)
        return sample.summary()
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{dataset}/{subject}/{filename}/epoch/{epoch_idx}", summary="Get a single epoch for inference")
def get_epoch(dataset: str, subject: str, filename: str, epoch_idx: int):
    """
    Returns a single 12-second epoch as a flat list for model inference.
    Shape: [1, 18, 2400] — ready to feed into BIOT/EEGNet.
    """
    try:
        sample = load_eeg_sample(dataset, subject, filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        epoch = sample.get_epoch(epoch_idx)  # [18, 2400]
    except IndexError as e:
        raise HTTPException(status_code=400, detail=str(e))

    label = sample.labels[epoch_idx] if epoch_idx < len(sample.labels) else None

    return {
        "dataset":   dataset,
        "subject":   subject,
        "file":      filename,
        "epoch_idx": epoch_idx,
        "label":     label,          # 0=background, 1=seizure
        "label_str": "seizure" if label == 1 else "background",
        "shape":     [1, 18, 2400],
        "data":      epoch.tolist(), # [18, 2400] nested list
    }


@router.get("/{dataset}/{subject}/{filename}/seizures", summary="Get all seizure epochs")
def get_seizure_epochs(
    dataset: str,
    subject: str,
    filename: str,
    limit: int = Query(10, description="Max number of seizure epochs to return"),
):
    """Returns seizure-labeled epochs for inspection/testing."""
    try:
        sample = load_eeg_sample(dataset, subject, filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    seiz_epochs = sample.get_seizure_epochs()
    n_total = seiz_epochs.shape[0]
    seiz_epochs = seiz_epochs[:limit]

    return {
        "n_seizure_epochs": n_total,
        "returned":         seiz_epochs.shape[0],
        "shape":            list(seiz_epochs.shape),
        "data":             seiz_epochs.tolist(),
    }
