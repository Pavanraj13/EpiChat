import torch
import torch.nn.functional as F
import sys
from pathlib import Path
import mne
import numpy as np
import warnings

# Suppress MNE verbose
warnings.filterwarnings("ignore", category=RuntimeWarning)
import os
os.environ.setdefault("MNE_LOGGING_LEVEL", "ERROR")
mne.set_log_level("ERROR")

sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from scripts.preprocess import map_channels, zero_pad_to_18, TARGET_SFREQ, EPOCH_SAMP, N_CHANNELS
from models.epichat_model import EpiChatModel

def test():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = EpiChatModel()
    model_path = Path(__file__).resolve().parent.parent.parent / "backend/model_weights/epichat_best.pt"
    if not model_path.exists():
        model_path = Path(__file__).resolve().parent.parent / "model_weights/epichat_best.pt"
        
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    
    file_path = Path("data/uploads/chb03_05.edf")
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return
        
    raw = mne.io.read_raw_edf(str(file_path), preload=True, verbose=False)
    raw_mapped = map_channels(raw.copy(), dataset="chbmit")
    if raw_mapped is None: return
    
    raw = raw_mapped
    available_channels = list(raw.ch_names)
    
    if abs(raw.info["sfreq"] - TARGET_SFREQ) > 0.5:
        raw.resample(TARGET_SFREQ, npad="auto")
        
    data = raw.get_data()
    data = zero_pad_to_18(data, available_channels)
    
    n_samples = data.shape[1]
    n_epochs = n_samples // EPOCH_SAMP
    data = data[:, : n_epochs * EPOCH_SAMP]
    epochs = data.reshape(n_epochs, N_CHANNELS, EPOCH_SAMP)
    
    probs_list = []
    with torch.no_grad():
        for i in range(n_epochs):
            epoch_data = epochs[i].astype(np.float32)
            x_tensor = torch.tensor(epoch_data, dtype=torch.float32).unsqueeze(0).to(device)
            outputs = model(x_tensor)
            probs = F.softmax(outputs, dim=1)
            probs_list.append(probs[0, 1].item())
            
    print(f"Total Epochs: {n_epochs}")
    print(f"Max Seizure Probability: {max(probs_list):.4f}")
    print(f"Mean Seizure Probability: {np.mean(probs_list):.4f}")
    
    # how many epochs passed 50%
    over_50 = sum(1 for p in probs_list if p > 0.5)
    print(f"Epochs > 50%: {over_50}")
    
    # how many epochs passed 5%
    over_5 = sum(1 for p in probs_list if p > 0.05)
    print(f"Epochs > 5%: {over_5}")
    
if __name__ == "__main__":
    test()
