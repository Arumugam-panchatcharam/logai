# gui/app_instance.py

import dash
import dash_bootstrap_components as dbc
from flask import Flask

flask_server = Flask(__name__)

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    title="LogAI",
    server=flask_server
)

(venv) sreedeviv@sreedevi logai % 
(venv) sreedeviv@sreedevi logai % 
(venv) sreedeviv@sreedevi logai % 
(venv) sreedeviv@sreedevi logai % 
(venv) sreedeviv@sreedevi logai % cat gui/demo/ai_broadband_faults.py 
# AI-Powered Broadband Fault Detection (Hybrid: ML + Local LLM)

# Requirements:
# - Python 3.x
# - `pandas`, `torch`, `sentence-transformers`, `faiss-cpu`, `scikit-learn`, `requests`, `matplotlib`

import os
import sys
import time
import json
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import IsolationForest
import requests
import matplotlib.pyplot as plt
from collections import defaultdict

# ─── Configuration ─────────────────────────────────────────────────

LOG_ROOTS = [arg for arg in sys.argv[1:] if not arg.startswith("--") and not arg.startswith("model=") and not arg.startswith("faults=")]
DATA_LOG = "/tmp/log_metrics.csv"
SUMMARY_FILE = "/tmp/llm_summary.txt"
SUMMARY_JSON = "/tmp/llm_summary.json"
OLLAMA_URL = "http://localhost:11434/api/generate"

model_arg = next((arg for arg in sys.argv if arg.startswith("model=")), None)
MODEL_LIST = model_arg.split("=", 1)[1].split(",") if model_arg else ["mistral"]

fault_arg = next((arg for arg in sys.argv if arg.startswith("faults=")), None)
fault_keywords = fault_arg.split("=", 1)[1].split(",") if fault_arg else ["timeout", "unreachable", "link down", "dns failure", "disconnect", "Radar detected"]

sent_cache = set()

device = "cuda" if torch.cuda.is_available() else "cpu"

# ─── Utilities ────────────────────────────────────────────────

def get_all_log_files(folders):
    log_files = []
    for folder in folders:
        for root, _, files in os.walk(folder):
            for name in files:
                log_files.append(os.path.join(root, name))
    return log_files

# ─── Step 1: Parse Logs and Store Fault Count ───────────────────────────

def parse_logs():
    ts = pd.Timestamp.now()
    fault_count = 0

    for file_path in get_all_log_files(LOG_ROOTS):
        if not os.path.isfile(file_path):
            continue

        try:
            with open(file_path, 'r', errors='ignore') as file:
                lines = file.readlines()
                fault_count += sum(any(kw.lower() in line.lower() for kw in fault_keywords) for line in lines)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    with open(DATA_LOG, "a") as f:
        f.write(f"{ts},{fault_count}\n")

# ─── Step 2: LSTM-based Fault Prediction ───────────────────────────

class FaultDataset(Dataset):
    def __init__(self, series, window_size):
        self.series = series
        self.window_size = window_size

    def __len__(self):
        return len(self.series) - self.window_size

    def __getitem__(self, idx):
        return (
            torch.tensor(self.series[idx:idx+self.window_size], dtype=torch.float32),
            torch.tensor(self.series[idx+self.window_size], dtype=torch.float32),
        )

class LSTMModel(nn.Module):
    def __init__(self, input_size=1, hidden_size=32, num_layers=2):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1, :])
def predict_fault():
    df = pd.read_csv(DATA_LOG, header=None, names=["ds", "faults"])
    df = df.tail(200)
    series = df["faults"].values.reshape(-1, 1)

    if len(series) < 20:
        print("Not enough data to make a fault prediction.")
        return False

    scaler = MinMaxScaler()
    scaled_series = scaler.fit_transform(series).flatten()

    model_iso = IsolationForest(contamination=0.05)
    anomalies = model_iso.fit_predict(series)
    df["anomaly"] = anomalies

    dataset = FaultDataset(scaled_series, window_size=10)
    if len(dataset) <= 0:
        print("Insufficient time-series data for LSTM prediction.")
        return False

    dataloader = DataLoader(dataset, batch_size=16, shuffle=False)

    model = LSTMModel().to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    model.train()
    for epoch in range(10):
        for x, y in dataloader:
            x = x.unsqueeze(-1).to(device)
            y = y.unsqueeze(-1).to(device)
            output = model(x)
            loss = criterion(output, y)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

    model.eval()
    x = torch.tensor(scaled_series[-10:], dtype=torch.float32).unsqueeze(0).unsqueeze(-1).to(device)
    with torch.no_grad():
        pred = model(x).cpu().item()

    fault_pred = scaler.inverse_transform([[pred]])[0][0]
    print("Predicted fault count:", fault_pred)
    return fault_pred > 5

# ─── Visualization ──────────────────────────────────────

# (no changes to visualization needed)

# ─── Step 3: Local LLM Summarization ───────────────────────────

def summarize_logs_with_llm(log_lines, model_name):
    unique_lines = list(set(log_lines))
    categorized = defaultdict(list)
    radar_contexts = []

    for line in unique_lines[-500:]:
        lowered = line.lower()
        if "radar detected" in lowered:
            idx = unique_lines.index(line)
            context = unique_lines[max(0, idx - 10):min(len(unique_lines), idx + 11)]
            radar_contexts.append("\n".join(context))
        for keyword in fault_keywords:
            if keyword in lowered:
                categorized[keyword].append(line.strip())
                break

    summary_input = ""
    for key, entries in categorized.items():
        summary_input += f"\n--- {key.upper()} ({len(entries)} occurrences) ---\n" + "\n".join(entries[:10])
    if radar_contexts:
        summary_input += "\n--- RADAR DETECTION CONTEXT ---\n" + "\n---\n".join(radar_contexts)

    prompt = f"""
You are a network fault diagnosis assistant.

Special Case:
- If any logs contain 'Radar detected', check the next 10 lines to see if a 'channel change' or 'frequency switch' is mentioned.
- If no such transition follows, flag it as a potential DFS handling issue.

Analyze the categorized system log lines and provide:
- Root Cause
- Resolution Steps
- Radar Scenario Note (if applicable)

{summary_input}

Response format:
Root Cause: ...
Resolution Steps: ...
Radar Detection Note: ...
"""

    payload = {
        "model": model_name,
        "prompt": prompt,
        "stream": False
    }

    try:
        res = requests.post(OLLAMA_URL, json=payload)
        res.raise_for_status()
        response_text = res.json().get("response", "[No response]")
        with open(SUMMARY_FILE, "a") as f:
            f.write(f"\n\n=== {model_name.upper()} SUMMARY @ {pd.Timestamp.now()} ===\n{response_text}\n")
        if os.path.exists(SUMMARY_JSON):
            with open(SUMMARY_JSON, "r") as jf:
                json_data = json.load(jf)
        else:
            json_data = {}
        json_data[model_name] = {
            "timestamp": str(pd.Timestamp.now()),
            "summary": response_text
        }
        with open(SUMMARY_JSON, "w") as jf:
            json.dump(json_data, jf, indent=2)

        return response_text
    except Exception as e:
        return f"[LLM Error: {e}]"

# ─── Main Loop ────────────────────────────────────

if __name__ == "__main__":
    print("🔍 Parsing logs...")
    parse_logs()

    print("📊 Predicting fault trends...")
    if predict_fault():
       print("⚠️  Anomaly detected in fault count.")

    print("🧠 Summarizing using LLM...")
    all_lines = []
    for file_path in get_all_log_files(LOG_ROOTS):
        try:
            with open(file_path, 'r', errors='ignore') as file:
                all_lines.extend(file.readlines())
        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    for model_name in MODEL_LIST:
         print(f"🤖 Generating summary with model: {model_name}")
         summary = summarize_logs_with_llm(all_lines, model_name)
         print(summary)
