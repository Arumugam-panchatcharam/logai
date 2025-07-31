# gui/pages/ai_analysis.py

import dash_bootstrap_components as dbc
from dash import html, dcc

layout = html.Div([
    html.H2("AI-based Log Analysis", className="text-center my-4"),

    dbc.Row([
        dbc.Col([
            html.Label("Log File Path"),
            dcc.Input(id="log-path-input", type="text", placeholder="Enter log file path", style={"width": "100%"}),
            html.Br(), html.Br(),

            html.Label("Model Name"),
            dcc.Dropdown(
                id="model-input",
                options=[{"label": m, "value": m} for m in ["mistral", "llama2"]],
                placeholder="Select or enter model",
                searchable=True,
                multi=False
            ),
            html.Br(),

            html.Label("Faults (comma-separated)"),
            dcc.Input(id="faults-input", type="text", placeholder="e.g., wifi_down,reset_failed", style={"width": "100%"}),
            html.Br(), html.Br(),

            dbc.Button("Run AI Analysis", id="run-ai-script-btn", color="primary"),
            html.Pre(id="ai-script-output", className="mt-3", style={
                "whiteSpace": "pre-wrap",
                "maxHeight": "500px",
                "overflowY": "auto"
            })
        ], width=8)
    ], justify="center")
])

