# EpiChat - Colab Pro Training Guide

This document contains everything you need to successfully train the EpiChat model on Google Colab Pro tomorrow. You can share this directly with your mentor.

## Prerequisites
1. Ensure your latest code is pushed to the `main` branch of `https://github.com/Pavanraj13/EpiChat.git`.
2. Ensure you have exact access to your Google Drive folder containing the preprocessed `.npy` files (e.g., `epichat_processed`).

---

## Step 1: Open Google Colab Pro
1. Navigate to: [Google Colab](https://colab.research.google.com/)
2. Create a **New Notebook**.
3. Go to the top menu: **Runtime > Change runtime type**.
4. Select **A100 GPU** or **V100 GPU** and make sure **High-RAM** is enabled.
5. Click **Save**.

---

## Step 2: Setup Environment & Clone Repo
Create a new cell, paste the following code, and run it. 
*(⚠️ **CRITICAL:** When it asks for Google Drive permission, be absolutely sure to select **YOUR OWN Google Account** where you uploaded the data, NOT the owner of the Colab Pro account! This ensures the weights are safely stored in your personal Google Drive).*

```python
# 1. Clone your EpiChat repo
!git clone https://github.com/Pavanraj13/EpiChat.git
%cd EpiChat

# 2. Install required AI & Medical dependencies
!pip install torch torchvision torchaudio mne scipy tqdm --quiet

# 3. Mount Google Drive so Colab can access your uploaded data
from google.colab import drive
drive.mount('/content/drive')
```

---

## Step 3: Copy Data to Colab Storage
Create a new cell. **Important:** Set the `DATA_SRC` variable to the exact path of your uploaded folder.

💡 **Pro Tip**: To get the exact path, click the **Folder icon** 📁 on the left sidebar of Colab. Expand `drive` -> `MyDrive`, find your data folder, click the three dots `⋮` next to it, and select **"Copy path"**.

```python
import shutil, os

# Paste your copied path below:
DATA_SRC = "/content/drive/MyDrive/YOUR_FOLDER_NAME"   
DATA_DST = "/content/EpiChat/data/processed"

print("Copying data to local fast storage... (This takes a few minutes)")
os.makedirs(DATA_DST, exist_ok=True)
shutil.copytree(DATA_SRC, DATA_DST, dirs_exist_ok=True)
print("Data ready for training!")
```

---

## Step 4: Run Training
Create a new cell and run this command to start the AI training. 

```bash
!python scripts/train.py \
  --data_dir /content/EpiChat/data/processed \
  --model_dir /content/EpiChat/backend/model_weights \
  --epochs 30 \
  --batch_size 128 \
  --lr 3e-4 \
  --colab
```

*Note: If for any reason you run out of GPU memory, change `--batch_size 128` to `--batch_size 64` and restart the cell.*

---

## Step 5: Save the Trained Weights
**CRITICAL:** Google Colab deletes all data when you close the tab. You **must** copy the trained model back to your Google Drive. 

Create a new cell and run:

```python
import shutil

# Copy the trained weights back to your personal Google Drive
shutil.copy(
    "/content/EpiChat/backend/model_weights/epichat_best.pt",
    "/content/drive/MyDrive/epichat_best_model.pt"
)
print("✅ Model successfully saved to your Google Drive!")
```

## Step 6: Using the Model Locally
After the session, download `epichat_best_model.pt` from your Google Drive and put it into your project folder at:
`backend/model_weights/epichat_best.pt`

Your FastAPI server will automatically load it and start making accurate Seizure Risk predictions on the dashboard.
