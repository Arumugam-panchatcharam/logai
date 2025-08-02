from dash import dash_table
from dash import Input, Output, callback
from gui.app_instance import app
from gui.diagnose_broadband import run_diagnosis

@callback(
    Output("ai-script-output", "children"),
    Input("run-ai-script-btn", "n_clicks"),
    prevent_initial_call=True,
)
def run_ai_script(n_clicks):
    result = run_diagnosis(
        model_dir="gui/assets/TinyLlama-1.1B-Chat-v1.0",
        test_file="app_uploaded_files/telemetry/Telemetry2_report.xlsx",
        column_file="column_list.txt"
    )
    # Render as Dash DataTable
    return dash_table.DataTable(
        data=result,
        columns=[
            {"name": "Time", "id": "Time"},
            {"name": "MAC", "id": "MAC"},
            {"name": "Diagnosis", "id": "Diagnosis"}
        ],
        style_table={
            "overflowX": "auto",
            "border": "1px solid #ccc",
        },
        style_cell={
            "textAlign": "left",
            "whiteSpace": "normal",
            "padding": "8px",
            "fontFamily": "Arial",
            "fontSize": "14px",
        },
        style_header={
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'black'
        },
        style_data={
            'backgroundColor': 'white',
            'color': 'black'
        },
        page_size=10,
    )

