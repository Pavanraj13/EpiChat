from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import os
import shutil
from pathlib import Path
import sys
import torch
import numpy as np
import warnings

# Suppress MNE verbose
warnings.filterwarnings("ignore", category=RuntimeWarning)
os.environ.setdefault("MNE_LOGGING_LEVEL", "ERROR")
try:
    import mne
    mne.set_log_level("ERROR")
except ImportError:
    pass

# Ensure scripts dir is in path to reuse BIOT preprocessing mappings
sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent))

from scripts.preprocess import map_channels, zero_pad_to_18, TARGET_SFREQ, EPOCH_SAMP, N_CHANNELS
from models.epichat_model import EpiChatModel

router = APIRouter()

# Setup Upload Cache Directories
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Load Model Globally
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = EpiChatModel()
model_path = Path(__file__).resolve().parent.parent.parent / "model_weights" / "epichat_best.pt"

try:
    if model_path.exists():
        checkpoint = torch.load(model_path, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        model.to(device)
        model.eval()
        print(f"EpiChat Model loaded successfully on {device}.")
    else:
        print(f"Warning: Model weights not found at {model_path}.")
except Exception as e:
    print(f"Failed to load model weights: {e}")

@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    # Validate Extension
    extension = file.filename.split(".")[-1].lower()
    if extension not in ["edf"]:
        raise HTTPException(status_code=400, detail="Invalid file type. Only .edf files are currently supported for AI inference.")
        
    try:
        # Cache file locally
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        print(f"File successfully received: {file.filename}")
        
        # Load and preprocess EDF
        try:
            raw = mne.io.read_raw_edf(str(file_path), preload=True, verbose=False)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to parse EDF: {e}")
            
        # Map Channels
        # We try mapping assuming CHBMIT nomenclature, if it fails try TUSZ
        raw_mapped = map_channels(raw.copy(), dataset="chbmit")
        if raw_mapped is None:
            raw_mapped = map_channels(raw.copy(), dataset="tusz")
            
        if raw_mapped is None:
            raise HTTPException(status_code=400, detail="File does not have the required EEG channels to process.")
        
        raw = raw_mapped
        available_channels = list(raw.ch_names)
        
        # Resample
        if abs(raw.info["sfreq"] - TARGET_SFREQ) > 0.5:
            raw.resample(TARGET_SFREQ, npad="auto")
            
        # Standardize matrix (Zero-Pad missing channels)
        data = raw.get_data()
        data = zero_pad_to_18(data, available_channels)
        
        # Epoch
        n_samples = data.shape[1]
        n_epochs = n_samples // EPOCH_SAMP
        
        if n_epochs == 0:
            raise HTTPException(status_code=400, detail=f"File is too short. Need at least 12 seconds of EEG data, found {n_samples/TARGET_SFREQ:.1f}s.")
            
        data = data[:, : n_epochs * EPOCH_SAMP]
        epochs = data.reshape(n_epochs, N_CHANNELS, EPOCH_SAMP)
        
        # Inference
        predict_seizure = False
        with torch.no_grad():
            for i in range(n_epochs):
                # Shape: (1, 18, 2400)
                epoch_data = epochs[i].astype(np.float32)
                x_tensor = torch.tensor(epoch_data, dtype=torch.float32).unsqueeze(0).to(device)
                
                outputs = model(x_tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                
                # Use a lowered sensitivity threshold of 5% because seizure events are heavily imbalanced.
                if probs[0, 1].item() > 0.05:
                    predict_seizure = True
                    break
                    
        result = "seizure" if predict_seizure else "healthy"

        return JSONResponse(status_code=200, content={"message": "Inference complete.", "filename": file.filename, "result": result})
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during inference: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred during inference: {e}")
