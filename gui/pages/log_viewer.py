import dash_bootstrap_components as dbc
from dash import dcc, html
from gui.pages.highlighter import TextHighlighter
from dash import Input, Output, State, ctx
import dash
import base64
import io
import os
# Configuration
LINES_PER_PAGE = 500
MAX_PAGINATION_PAGES = 15
MAX_FILE_SIZE_MB = 100

AUTO_SAVE_INTERVAL = 3000  # 3 seconds in milliseconds

UPLOAD_AREA_STYLE = {
    'border': '2px dashed #dee2e6',
    'border-radius': '8px',
    'padding': '20px',
    'text-align': 'center',
    'background': "#3b5c7d"
}

# Styles
SECTION_STYLE = {
    'border': '2px solid #dee2e6',
    'border-radius': '15px',
    'margin-bottom': '20px'
}

CODE_STYLE = {
    'background': '#2d3748',
    'color': '#e2e8f0',
    'padding': '15px',
    'border-radius': '8px',
    'font-family': 'monospace',
    'font-size': '12px',
    'height': '400px',
    'overflow-y': 'auto',
    'white-space': 'pre-wrap'
}

UPLOAD_STYLE = {
    'border': '2px dashed #dee2e6',
    'border-radius': '8px',
    'padding': '20px',
    'text-align': 'center',
    'background': '#f8f9fa',
    'min-height': '100px'
}
def create_log_viewer_layout():
    return html.Div([
    # 1. UPLOAD AREA (Collapsible - Top)
    dbc.Card([
        dbc.CardHeader([
            dbc.Button([
                html.I(id="upload-icon", className="fas fa-chevron-down me-2"),
                html.I(className="fas fa-cloud-upload-alt me-2"),
            ], id="toggle-upload", color="link", className="w-100 text-start")
        ]),
        dbc.Collapse([
            dbc.CardBody([
                dcc.Upload(
                    id='file-upload',
                    children=html.Div([
                        html.H5("Drag & Drop Files Here"),
                        html.P("Or click to browse", className="text-muted"),
                    ], style=UPLOAD_STYLE),
                    multiple=True
                ),
                html.Div(id="upload-feedback")
            ])
        ], id="upload-collapse", is_open=True)
    ], style=SECTION_STYLE),

    # 2. MAIN CONTROLS (Collapsible - File Explorer | Search | Notes)
    dbc.Card([
        dbc.CardHeader([
            dbc.Button([
                html.I(id="main-icon", className="fas fa-chevron-down me-2"),
                html.I(className="fas fa-th-large me-2"),
            ], id="toggle-main", color="link", className="w-100 text-start")
        ]),
        dbc.Collapse([
            dbc.CardBody([
                dbc.Row([
                    # File Explorer Column (Left)
                    dbc.Col([
                        dbc.Row([
                            dbc.Col([
                            html.H6([
                            html.I(className="fas fa-folder-tree me-2"),
                            "File Explorer"
                            ]),
                            ]),
                            dbc.Col(dbc.Button(html.I(className="fas fa-sync-alt"), id="refresh-files-icon", size="sm"))
                        ], className="mb-2"),
                        dbc.Row([
                        html.Small(id="file-stats", className="text-muted mb-3"),
                        html.Div(id="file-list", style={"max-height": "200px", "overflow-y": "auto"}),
                        ]),
                    ], width=4),
                    
                    # Search Column (Middle)
                    dbc.Col([
                        html.H6([
                            html.I(className="fas fa-search me-2"),
                            "Search"
                        ]),
                        dbc.InputGroup([
                            dbc.Input(id="search-input", placeholder="Search pattern", size="sm"),
                            dbc.Button("Go", id="search-btn", size="sm", color="primary")
                        ], className="mb-3"),
                        html.H6("Quick Patterns:", className="small mb-2"),
                        dbc.ButtonGroup([
                            dbc.Button("ERROR", id="btn-error", size="sm", color="outline-danger"),
                            dbc.Button("WARN", id="btn-warn", size="sm", color="outline-warning")
                        ], className="w-100 mb-2"),
                        dbc.ButtonGroup([
                            dbc.Button("IP", id="btn-ip", size="sm", color="outline-info"),
                            dbc.Button("Time", id="btn-time", size="sm", color="outline-secondary")
                        ], className="w-100")
                    ], width=4),
                    
                    # Notes Column (Right)
                    dbc.Col([
                        html.H6([
                            html.I(className="fas fa-sticky-note me-2 text-warning"),
                            "Notes"
                        ]),
                        html.Small(id="notes-info", className="text-muted mb-3"),
                        dbc.Textarea(
                            id="notes-area",
                            placeholder="Write analysis notes...\n\nDocument patterns, errors, findings.\nAuto-saves every 3 seconds.",
                            style={'height': '200px', 'font-size': '12px'}
                        ),
                        html.Div([
                            html.Small(id="save-status", className="text-success"),
                            html.Small(id="char-count", className="text-muted float-end")
                        ], className="mt-2")
                    ], width=4)
                ])
            ])
        ], id="main-collapse", is_open=True)
    ], style=SECTION_STYLE),

    # 3. FILE CONTENT VIEW (Collapsible)
    dbc.Card([
        dbc.CardHeader([
            dbc.Button([
                html.I(id="content-icon", className="fas fa-chevron-down me-2"),
                html.I(className="fas fa-file-alt me-2"),
                "File Content View"
            ], id="toggle-content", color="link", className="w-100 text-start")
        ]),
        dbc.Collapse([
            dbc.CardBody([
                html.Div(id="file-header"),
                html.Div(id="file-content"),
                html.Div(id="pagination-controls")
            ])
        ], id="content-collapse", is_open=True)
    ], style=SECTION_STYLE),
    
    # 4. SEARCH VIEW (Collapsible)
    dbc.Card([
        dbc.CardHeader([
            dbc.Button([
                html.I(id="search-view-icon", className="fas fa-chevron-down me-2"),
                html.I(className="fas fa-search-plus me-2"),
                "Search View"
            ], id="toggle-search-view", color="link", className="w-100 text-start")
        ]),
        dbc.Collapse([
            dbc.CardBody([
                html.Div(id="search-results")
            ])
        ], id="search-view-collapse", is_open=True)
    ], style=SECTION_STYLE)
    ])

layout = create_log_viewer_layout()