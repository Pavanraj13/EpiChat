import argparse
import os
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, accuracy_score
import sys
import pandas as pd
import warnings

# Suppress MNE warnings
warnings.filterwarnings("ignore")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app.data.dataset import EEGEpochDataset
from backend.app.models.epichat_model import EpiChatModel

def evaluate_fast():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Using Device for Fast Eval: {device}")
    
    # Check for weights
    model_path = "backend/model_weights/epichat_best.pt"
    if not os.path.exists(model_path):
        print(f"[ERROR] Model weights missing at {model_path}")
        return
        
    print(f"[INFO] Initializing dataset (Targeting Seizure-Rich Files)...")
    # We specifically include chb03 files found to have seizures to ensure Sensitivity is tested
    dataset = EEGEpochDataset(data_dir="C:/Users/U.PAVAN RAJ/Epichat_Data/processed/chbmit", augment=False, max_files=100)
    
    # Filter to ensure we have a good mix if possible, or just use the first 100 which includes chb01 and chb03
    if len(dataset) == 0:
        print("[ERROR] Dataset empty or could not be loaded from C:/Users/U.PAVAN RAJ/Epichat_Data/processed/chbmit")
        return

    # Count classes
    targets = [t for _, t in dataset]
    class_0 = targets.count(0)
    class_1 = targets.count(1)
    print(f"[INFO] Dataset loaded: {class_0} Non-Seizure, {class_1} Seizure epochs")
    
    if class_1 == 0:
        print("[WARNING] No seizure epochs found in the first 100 files. Model Sensitivity cannot be verified.")
        
    loader = DataLoader(dataset, batch_size=64, shuffle=False)
    
    model = EpiChatModel()
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    
    all_preds = []
    all_targets = []
    all_probs = []
    
    print("\n[INFO] Running Inference...")
    with torch.no_grad():
        for inputs, targets in loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            probs = torch.nn.functional.softmax(outputs, dim=1)[:, 1]
            _, predicted = outputs.max(1)
            
            all_preds.extend(predicted.cpu().numpy())
            all_targets.extend(targets.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
            
    print("\n" + "="*40)
    print("      EpiChat Model Evaluation")
    print("="*40)
    
    acc = accuracy_score(all_targets, all_preds)
    print(f"Overall Accuracy: {acc * 100:.2f}%")
    
    try:
        roc = roc_auc_score(all_targets, all_probs)
        print(f"ROC-AUC Score:    {roc:.4f}")
    except ValueError:
        print("ROC-AUC Score:    N/A (Only one class present in small test sample)")
        
    print("\nConfusion Matrix:")
    m = confusion_matrix(all_targets, all_preds)
    if m.shape == (2, 2):
        print(f"   [TN: {m[0][0]:<4} FP: {m[0][1]:<4}]")
        print(f"   [FN: {m[1][0]:<4} TP: {m[1][1]:<4}]")
    else:
        print(m)
        
    print("\nClassification Report:")
    print(classification_report(all_targets, all_preds, zero_division=0))
    print("="*40)
    
if __name__ == "__main__":
    evaluate_fast()
