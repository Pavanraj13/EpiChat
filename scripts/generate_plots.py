import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import confusion_matrix, roc_curve, auc
import matplotlib.pyplot as plt
import seaborn as sns
import sys
import numpy as np

# Ensure backend imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app.data.dataset import EEGEpochDataset
from backend.app.models.epichat_model import EpiChatModel

def generate_visual_metrics():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Using Device: {device}")
    
    # 1. Setup paths
    model_path = "backend/model_weights/epichat_realistic.pt"
    assets_dir = "backend/assets"
    os.makedirs(assets_dir, exist_ok=True)
    
    if not os.path.exists(model_path):
        print(f"[ERROR] Model weights missing at {model_path}")
        return
        
    # 2. Load Model
    print(f"[INFO] Loading Model: {model_path}")
    model = EpiChatModel(num_channels=18, num_samples=2400, num_classes=2).to(device)
    checkpoint = torch.load(model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    # 3. Load Dataset (Sample for visualization speed)
    print(f"[INFO] Initializing dataset for visualization...")
    dataset = EEGEpochDataset(data_dir="C:/Users/U.PAVAN RAJ/Epichat_Data/processed/chbmit", augment=False, max_files=100)
    loader = DataLoader(dataset, batch_size=128, shuffle=False)
    
    all_targets = []
    all_probs = []
    all_preds = []
    
    print("[INFO] Running Inference...")
    with torch.no_grad():
        for inputs, targets in loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            probs = torch.nn.functional.softmax(outputs, dim=1)[:, 1]
            _, predicted = outputs.max(1)
            
            all_targets.extend(targets.cpu().numpy())
            all_probs.extend(probs.cpu().numpy())
            all_preds.extend(predicted.cpu().numpy())
            
    # 4. Generate Confusion Matrix Plot
    print("[INFO] Generating Confusion Matrix...")
    cm = confusion_matrix(all_targets, all_preds)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=['Healthy', 'Seizure'], yticklabels=['Healthy', 'Seizure'])
    plt.title('EpiChat Seizure Detection - Confusion Matrix')
    plt.ylabel('Clinical Ground Truth')
    plt.xlabel('AI Predicted State')
    cm_path = os.path.join(assets_dir, "confusion_matrix.png")
    plt.savefig(cm_path)
    plt.close()
    
    # 5. Generate ROC Curve Plot
    print("[INFO] Generating ROC Curve...")
    fpr, tpr, _ = roc_curve(all_targets, all_probs)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.4f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate (FPR)')
    plt.ylabel('True Positive Rate (TPR / Sensitivity)')
    plt.title('EpiChat Model Performance - Receiver Operating Characteristic (ROC)')
    plt.legend(loc="lower right")
    plt.grid(alpha=0.3)
    roc_path = os.path.join(assets_dir, "roc_curve.png")
    plt.savefig(roc_path)
    plt.close()
    
    print(f"\n[SUCCESS] Visual metrics generated in {assets_dir}/")
    print(f"[*] Confusion Matrix: {cm_path}")
    print(f"[*] ROC Curve:        {roc_path}")

if __name__ == "__main__":
    generate_visual_metrics()
