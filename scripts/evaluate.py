import argparse
import os
import torch
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app.data.dataset import EEGEpochDataset
from backend.app.models.epichat_model import EpiChatModel

def evaluate_model(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[INFO] Using Device: {device} for Evaluation")
    
    # 1. Dataset Config
    print(f"[INFO] Initializing dataset from: {args.data_dir}")
    dataset = EEGEpochDataset(data_dir=args.data_dir, augment=False)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=False, num_workers=2)
    
    if len(dataset) == 0:
        print("[ERROR] Dataset missing.")
        return
        
    # 2. Load Model Checkpoint
    model = EpiChatModel()
    
    if not os.path.exists(args.model_path):
        print(f"[ERROR] Could not find model weights at: {args.model_path}")
        return
        
    checkpoint = torch.load(args.model_path, map_location=device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(device)
    model.eval()
    
    all_preds = []
    all_targets = []
    
    print("\n[INFO] Running Inference Engine...")
    with torch.no_grad():
        for inputs, targets in loader:
            inputs, targets = inputs.to(device), targets.to(device)
            outputs = model(inputs)
            _, predicted = outputs.max(1)
            
            all_preds.extend(predicted.cpu().numpy())
            all_targets.extend(targets.cpu().numpy())
            
    # 3. Metrics Synthesis
    print("\n--- EpiChat Evaluation Report ---")
    print(classification_report(all_targets, all_preds, target_names=["Background", "Seizure"]))
    
    m = confusion_matrix(all_targets, all_preds)
    print("Confusion Matrix:")
    print(f"TN: {m[0][0]} | FP: {m[0][1]}")
    print(f"FN: {m[1][0]} | TP: {m[1][1]}")
    
    # Save Results
    os.makedirs("results", exist_ok=True)
    df = pd.DataFrame({'Target': all_targets, 'Prediction': all_preds})
    df.to_csv("results/cv_results.csv", index=False)
    print("\n[*] Analysis saved to results/cv_results.csv")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EpiChat Model Evaluation")
    parser.add_argument("--data_dir", type=str, default="C:/Users/U.PAVAN RAJ/Epichat_Data/processed")
    parser.add_argument("--model_path", type=str, default="backend/model_weights/epichat_best.pt")
    parser.add_argument("--batch_size", type=int, default=64)
    args = parser.parse_args()
    
    evaluate_model(args)
