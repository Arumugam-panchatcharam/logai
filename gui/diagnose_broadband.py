import pandas as pd
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def load_selected_columns(column_file: str) -> list:
    with open(column_file, "r") as f:
        return [line.strip() for line in f if line.strip()]

def run_diagnosis(model_dir: str, test_file: str, column_file: str = "column_list.txt"):
    # === Load model ===
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForCausalLM.from_pretrained(model_dir)

    # === Load required columns from file ===
    required_columns = load_selected_columns(column_file)

    # === Read Excel file and select only required columns ===
    df = pd.read_excel(test_file, engine="openpyxl")
    df = df[[col for col in required_columns if col in df.columns]]
    df = df.astype(str).apply(lambda x: x.str.strip())


    # ✅ Initialize results list here
    results = []

    # === Run inference ===
    for idx, row in df.iterrows():

        instruction = "Diagnose broadband anomaly"
        input_text = (
            f"Time: {row.get('Report.Time', 'NA')}, "
            f"MAC: {row.get('Report.mac', 'NA')}, "
            f"WiFi1: {row.get('Report.Device.WiFi.SSID.1.Status', 'NA')}, "
            f"WiFi2: {row.get('Report.Device.WiFi.SSID.2.Status', 'NA')}, "
            f"Radio1: {row.get('Report.Device.WiFi.Radio.1.Status', 'NA')}, "
            f"Radio2: {row.get('Report.Device.WiFi.Radio.2.Status', 'NA')}, "
        )
        prompt = f"### Instruction:\n{instruction}\n\n### Input:\n{input_text}\n\n### Response:\n"
        inputs = tokenizer(prompt, return_tensors="pt").to("cpu")

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=100,
                do_sample=True,
                temperature=0.7,
                top_k=50,
                top_p=0.95,
                pad_token_id=tokenizer.eos_token_id,
            )

        full_output = tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = full_output.split("### Response:")[-1].strip()

        results.append({
            "Time": row.get("Report.Time", "NA"),
            "MAC": row.get("Report.mac", "NA"),
            "Diagnosis": response
        })

    return results

