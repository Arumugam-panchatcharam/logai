import dash_bootstrap_components as dbc
from dash import dcc, html
 
from .utils import (
    create_modal,
    create_description_card,
    create_upload_file_layout,
    create_file_setting_layout,
    create_param_table,
    create_run_button
)
 
 
"""def create_control_card():
    return html.Div(
        id="control-card",
        children=[
            create_upload_file_layout(),
            create_file_setting_layout(),
            create_summarization_algo_setting_layout(),
            html.Hr(),
            create_run_button("pattern-btn"),
            create_modal(
                modal_id="pattern_exception_modal",
                header="An Exception Occurred",
                content="An exception occurred. Please click OK to continue.",
                content_id="pattern_exception_modal_content",
                button_id="pattern_exception_modal_close",
            ),
        ],
    )"""
def create_ai_analysis_layout():
    return dbc.Row(
        [
            # Left column
            dbc.Col(
                html.Div(
                    [
                        create_description_card(),
                        #create_control_card(),
                        html.Div(
                            ["initial child"],
                            id="output-clientside",
                            style={"display": "none"},
                        ),
                    ]
                ),
                width=2,
            ),
            # Right column
            dbc.Col(
                html.Div(
                    [
                    dbc.Row([
                        dbc.Col([
                              dbc.Button("Run AI Analysis", id="run-ai-script-btn", color="primary"),
                              html.Pre(id="ai-script-output", className="mt-3", style={
                              "whiteSpace": "pre-wrap",
                              "maxHeight": "500px",
                              "overflowY": "auto"
                             })
                     ], width=8)
    ], justify="center")
    ])
 )
]
)
layout = create_ai_analysis_layout()
