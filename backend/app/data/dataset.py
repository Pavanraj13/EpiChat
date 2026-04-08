import os
import json
import torch
from torch.utils.data import Dataset
import numpy as np
from pathlib import Path

class EEGEpochDataset(Dataset):
    """
    Loads preprocessed Multi-Channel EEG Epochs (.npy) and labels.
    Expected Input Shape: (18, 2400) -> 18 Channels, 12 seconds @ 200Hz.
    Labels: 1 = Seizure, 0 = Background.
    """
    def __init__(self, data_dir: str, augment: bool = False, max_files: int = None):
        self.data_dir = Path(data_dir)
        self.augment = augment
        
        self.epoch_files = []
        self.labels = []
        self.subject_ids = []   # Track subjects
        self.file_ids = []      # New: Track specific recording files
        
        # Iteratively load all .json metadata files
        if not self.data_dir.exists():
            print(f"Warning: {data_dir} does not exist.")
            return

        meta_files = list(self.data_dir.rglob("*_meta.json"))
        
        for i, meta_file in enumerate(meta_files):
            if max_files is not None and i >= max_files:
                break
                
            npy_file = meta_file.with_name(meta_file.stem.replace('_meta', '') + '.npy')
            if not npy_file.exists():
                continue
            
            # Extract Subject ID (e.g., "chb01") and File ID (e.g., "chb01_03")
            subject_id = meta_file.stem.split('_')[0]
            file_id = meta_file.stem.replace('_meta', '')
            
            with open(meta_file, 'r') as f:
                meta = json.load(f)
            
            # Map index to individual epoch inside the .npy file
            for i, label in enumerate(meta['labels']):
                self.epoch_files.append((npy_file, i))
                self.labels.append(label)
                self.subject_ids.append(subject_id)
                self.file_ids.append(file_id)

    def __len__(self):
        return len(self.epoch_files)

    def _apply_augmentations(self, x: np.ndarray) -> np.ndarray:
        """
        Applies time-series domain augmentations.
        """
        # Random channel dropping (p=0.1) -> helps make model robust to bad electrodes
        if np.random.rand() < 0.1:
            drop_idx = np.random.randint(0, x.shape[0])
            x[drop_idx, :] = 0.0
            
        # Gaussian Noise injection -> better generalization
        if np.random.rand() < 0.3:
            noise = np.random.normal(0, np.std(x) * 0.1, x.shape)
            x = x + noise
            
        return x

    def __getitem__(self, idx):
        file_path, epoch_idx = self.epoch_files[idx]
        
        # mmap_mode allows us to read a single epoch locally from disk without OOM
        try:
            mmap_data = np.load(str(file_path), mmap_mode='r')
            epoch_data = mmap_data[epoch_idx].astype(np.float32)
        except Exception as e:
            # Fallback for weird edge cases
            epoch_data = np.zeros((18, 2400), dtype=np.float32)

        if self.augment:
            epoch_data = self._apply_augmentations(epoch_data)
        
        label = self.labels[idx]
        
        # Output shape: [18, 2400]
        x_tensor = torch.tensor(epoch_data, dtype=torch.float32)
        y_tensor = torch.tensor(label, dtype=torch.long)
        
        return x_tensor, y_tensor
