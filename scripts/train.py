import argparse
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from tqdm import tqdm
import sys

# Ensure backend imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.app.data.dataset import EEGEpochDataset
from backend.app.models.epichat_model import EpiChatModel

def get_device():
    if torch.cuda.is_available():
        return torch.device("cuda")
    elif torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")

def train_model(args):
    device = get_device()
    print(f"[INFO] Using Device: {device}")
    
    # 1. Dataset & DataLoader Setup
    # Assumes data corresponds to preprocessing script bounds
    print(f"[INFO] Initializing PyTorch Dataset from: {args.data_dir}")
    full_dataset = EEGEpochDataset(data_dir=args.data_dir, augment=True, max_files=100 if args.prototype else None)
    
    if len(full_dataset) == 0:
        print("[ERROR] Dataset is empty! Ensure preprocessing has completed.")
        return
        
    print(f"[INFO] Found {len(full_dataset)} total EEG epochs.")
    
    val_size = int(0.2 * len(full_dataset))
    train_size = len(full_dataset) - val_size
    
    # We use a fixed generator seed for reproducibility
    train_dataset, val_dataset = random_split(
        full_dataset, [train_size, val_size], generator=torch.Generator().manual_seed(42)
    )
    
    # DataLoader tuning for RTX 3050 & Colab Pro
    # Increased num_workers in Colab speeds up loading
    num_workers = 4 if args.colab else 0 
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True, 
                              num_workers=num_workers, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False, 
                            num_workers=num_workers, pin_memory=True)

    # 2. Model, Loss, Optimizer
    model = EpiChatModel(num_channels=18, num_samples=2400, num_classes=2).to(device)
    
    # Using pos_weight in CrossEntropy is extremely vital for Medical Imbalanced Data (less seizures)
    # We approximate Seizures are 5x to 10x less frequent
    weights = torch.tensor([1.0, 5.0]).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights)
    
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scaler = torch.cuda.amp.GradScaler() if device.type == 'cuda' else None
    
    os.makedirs(args.model_dir, exist_ok=True)
    best_val_loss = float('inf')
    
    print("\n[INFO] Starting Training Loop...")
    for epoch in range(1, args.epochs + 1):
        # -- TRAIN STAGE --
        model.train()
        train_loss = 0.0
        correct = 0
        total = 0
        
        # tqdm for pretty Colab logging
        pbar = tqdm(train_loader, desc=f"Epoch {epoch}/{args.epochs} [TRAIN]")
        for batch_idx, (inputs, targets) in enumerate(pbar):
            inputs, targets = inputs.to(device), targets.to(device)
            
            # Forward pass with AMP for lower VRAM footprints 
            # (especially important for local RTX 3050 4GB/8GB)
            if scaler:
                with torch.cuda.amp.autocast():
                    outputs = model(inputs)
                    loss = criterion(outputs, targets)
                
                # Gradient Accumulation Logic
                scaler.scale(loss).backward()
                
                if (batch_idx + 1) % args.accum_steps == 0 or (batch_idx + 1) == len(train_loader):
                    scaler.step(optimizer)
                    scaler.update()
                    optimizer.zero_grad(set_to_none=True)
            else:
                outputs = model(inputs)
                loss = criterion(outputs, targets)
                loss.backward()
                
                if (batch_idx + 1) % args.accum_steps == 0 or (batch_idx + 1) == len(train_loader):
                    optimizer.step()
                    optimizer.zero_grad()

            train_loss += loss.item()
            _, predicted = outputs.max(1)
            total += targets.size(0)
            correct += predicted.eq(targets).sum().item()
            
            pbar.set_postfix({'loss': f"{train_loss/(batch_idx+1):.4f}", 'acc': f"{100.*correct/total:.2f}%"})
            
        # -- VALIDATION STAGE --
        model.eval()
        val_loss = 0.0
        v_correct = 0
        v_total = 0
        
        with torch.no_grad():
            vpbar = tqdm(val_loader, desc=f"Epoch {epoch}/{args.epochs} [VAL]")
            for inputs, targets in vpbar:
                inputs, targets = inputs.to(device), targets.to(device)
                
                # Inference AMP
                if scaler:
                    with torch.cuda.amp.autocast():
                        outputs = model(inputs)
                        loss = criterion(outputs, targets)
                else:
                    outputs = model(inputs)
                    loss = criterion(outputs, targets)
                    
                val_loss += loss.item()
                _, predicted = outputs.max(1)
                v_total += targets.size(0)
                v_correct += predicted.eq(targets).sum().item()
                
        avg_val_loss = val_loss / len(val_loader)
        val_acc = 100. * v_correct / v_total
        print(f"--- Epoch {epoch} Results: Val Loss: {avg_val_loss:.4f} | Val Acc: {val_acc:.2f}% ---")
        
        # Checkpointing
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            save_path = os.path.join(args.model_dir, "epichat_best.pt")
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'val_loss': best_val_loss,
            }, save_path)
            print(f"[*] New best model saved to {save_path}")
            
    print("\n[INFO] Training Complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EpiChat Hybrid BIOT+EEGNet Training Script")
    parser.add_argument("--data_dir", type=str, default="C:/Users/U.PAVAN RAJ/Epichat_Data/processed", help="Path to preprocessed .npy files")
    parser.add_argument("--model_dir", type=str, default="backend/model_weights", help="Where to save model pt")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch_size", type=int, default=32, help="Set to 16 for RTX3050, 128 for Colab Pro A100")
    parser.add_argument("--lr", type=float, default=3e-4)
    parser.add_argument("--accum_steps", type=int, default=1, help="Gradient accumulation steps for small VRAM")
    parser.add_argument("--colab", action="store_true", help="Enable Colab optimizations (more workers, etc)")
    parser.add_argument("--prototype", action="store_true", help="Train on a small subset (100 files) for fast prototyping")
    
    args = parser.parse_args()
    
    train_model(args)
