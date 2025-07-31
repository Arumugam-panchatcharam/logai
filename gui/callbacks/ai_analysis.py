# gui/callbacks/ai_analysis.py

from dash import Input, Output, State
import subprocess
import os
from gui.app_instance import app

@app.callback(
    Output("ai-script-output", "children"),
    Input("run-ai-script-btn", "n_clicks"),
    State("log-path-input", "value"),
    State("model-input", "value"),
    State("faults-input", "value"),
    prevent_initial_call=True,
)
def run_ai_script(n_clicks, log_path, model_name, faults_str):
    try:
        script_path = os.path.join("gui", "demo", "ai_broadband_faults.py")
        if not os.path.isfile(script_path):
            return f"[Error] Script not found: {script_path}"
        if not log_path or not model_name or not faults_str:
            return "[Error] Please fill all inputs."

        model_param = f"model={model_name}"
        faults_param = f"faults={faults_str}"

        command = [
            "python3",
            script_path,
            log_path,
            model_param,
            faults_param
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout or "[No Output]"

    except subprocess.CalledProcessError as e:
        return f"[Error] Script failed:\n{e.stderr}"
    except Exception as e:
        return f"[Unexpected Error] {str(e)}"
