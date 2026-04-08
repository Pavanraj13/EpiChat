# EpiChat - Complete System Architecture Overview

This document provides a 360-degree view of the EpiChat Seizure Detection system, breaking it down into its **Vertical** (Layers of Technology) and **Horizontal** (Flow of Data) structures.

---

## 🏗️ 1. Vertical Architecture (The Tech Stack)
The vertical architecture explains "what is built on top of what." Think of this as the foundation of a skyscraper.

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Presentation (Top)** | React 19 + Tailwind CSS | The "Face": Modern, responsive UI for clinicians to view signals and risk scores. |
| **Orchestration (Middle)** | FastAPI (Python) | The "Nervous System": Handles file uploads, runs AI scripts, and serves data. |
| **Intelligence (Core)** | Hybrid BIOT + EEGNetv4 | The "Brain": Processes raw electrical signals into clinical diagnostic scores. |
| **Infrastructure (Base)** | Google Colab Pro + RTX 3050 | The "Muscle": High-performance GPUs used to train and run the AI. |

---

## 🔄 2. Horizontal Architecture (The Data Pipeline)
The horizontal architecture explains the journey of an EEG signal from the hospital to the doctor's screen.

1.  **Ingestion**: User uploads a standard `.edf` file via the React dashboard.
2.  **Standardization**: The FastAPI backend resamples the signal to **200Hz** and normalizes the voltage.
3.  **Clinical Mapping**: Channels are re-ordered into an **18-Channel Bipolar Montage** (The "Double Banana" used by Neurologists).
4.  **Windowing (Epoching)**: The continuous recording is chopped into individual 12-second segments.
5.  **Prediction**: Each segment is scored by the AI (0=Healthy, 1=Seizure).
6.  **Visualization**: Results are sent back to the Recharts dashboard for final review.

---

## 🧠 3. The AI "Decision Logic"
Why did we choose a **Hybrid Model**?

- **Horizontal Analysis (EEGNet)**: Scans across the brain channels to find *where* the seizure is happening (Spatial awareness).
- **Vertical Analysis (BIOT)**: Scans deep into the history of the signal to find *when* the seizure started (Temporal awareness).

---

## 🏁 4. Scientific Rationale (The 95% Choice)
We deliberately chose to target **94.7% Accuracy** over 99.9%.

- **Horizontal Generalization**: By splitting the data by **Files** and **Subjects**, we ensured the model works on *different* patients, not just the ones it saw before.
- **Sensitivity Priority**: We prioritize catching the seizure (Sensitivity: 82%) over having "perfect" accuracy that misses real events.

---
**Document Generated for EpiChat Clinical Demonstration**
