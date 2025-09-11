import dash_bootstrap_components as dbc
import dash
from dash import ctx
from dash import html, Input, Output, State, callback
from gui.file_manager import FileManager
from gui.pages.highlighter import TextHighlighter
import base64
import os
import re
from pathlib import Path
import shutil
from datetime import datetime
from dash import dcc
from dash.dependencies import ALL
import math
import json
import glob

from logai.utils.constants import (
    BASE_DIR, 
    MERGED_LOGS_DIR_NAME,
    MERGED_LOGS_ARCHIVE_NAME,
    TELEMETRY_PROFILES_DIR_NAME,
    LINES_PER_PAGE, UPLOAD_DIRECTORY
)

from gui.app_instance import dbm

CODE_STYLE = {
    'background': '#2d3748',
    'color': '#e2e8f0',
    'padding': '15px',
    'border-radius': '8px',
    'font-family': 'monospace',
    'font-size': '12px',
    'height': '500px',
    'overflow-y': 'auto',
    'white-space': 'pre-wrap'
}

def no_files_uploaded():
    return html.Div([
            html.I(className="fas fa-file fa-2x text-muted mb-2"),
            html.P("No files uploaded yet", className="text-muted")
        ], className="text-center py-3")
    
# FILE UPLOAD
@callback(
    [Output('file-list', 'children'),
     Output('file-stats', 'children')
     ],
    [Input('file-upload', 'contents'), 
     Input("current-project-store", "data"),
     Input('refresh-files-icon', 'n_clicks')],
    [State('file-upload', 'filename')],
)
def handle_upload(contents_list, project_data, refresh_clicks, filenames_list):
    if not project_data or not project_data.get("project_id"):
        return html.P([html.I(className="fas fa-info-circle me-2"), "No project selected"], className="text-muted"), "0 files"
    
    project_id = project_data["project_id"]
    project_name = project_data["project_name"]
    user_id = project_data.get("user_id")


    if ctx.triggered_id == 'file-upload':
        if contents_list and filenames_list:
            if not isinstance(contents_list, list):
                contents_list = [contents_list]
                filenames_list = [filenames_list]
            
            results = []
            for content, filename in zip(contents_list, filenames_list):
                content_type, content_string = content.split(',')
                decoded = base64.b64decode(content_string)

                project_dir = Path(f'{UPLOAD_DIRECTORY}/{user_id}/{project_id}')
                project_dir.mkdir(parents=True, exist_ok=True)
                file_path = project_dir / filename

                with open(file_path, 'wb') as f:
                    f.write(decoded)
            
            # process the uploadd files
            file_manager = FileManager()
            file_manager.process_uploaded_files(project_dir, project_name)

            for files in os.listdir(project_dir/MERGED_LOGS_DIR_NAME):
                dbm.save_local_file(Path(project_dir/MERGED_LOGS_DIR_NAME/files), project_id)
            
            archive = glob.glob(os.path.join(project_dir, '*.zip'))
            for file in archive:
                print("archive file name", file)
                if os.path.exists(project_dir/file):
                    dbm.save_local_file(Path(project_dir/file), project_id)
            
            # clean up the project directory
            shutil.rmtree(project_dir/MERGED_LOGS_DIR_NAME)

            feedback = dbc.Alert([html.P(r, className="mb-0 small") for r in results], 
                            color="success" if all("✅" in r for r in results) else "warning")
    
    # remove the uploaded files after processing
    files = dbm.get_project_files(project_id)
    #print("Project file",files)

    if not files:
        return html.Div([
            html.I(className="fas fa-file fa-2x text-muted mb-2"),
            html.P("No files uploaded yet", className="text-muted")
        ], className="text-center py-3"), "0 files"

    file_items = []
    for filename, _, original_name, file_size, _ in files:
        size_mb = round(file_size / (1024 * 1024), 2) if file_size else 0
        download_url = f"/download/{project_id}/{filename}"

        non_text_extensions = ['.xls', '.xlsx', '.tgz', '.zip']
        is_viewable = any(original_name.lower().endswith(ext) for ext in non_text_extensions) == False

        item = dbc.ListGroupItem([
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-file-alt me-2 text-primary" if is_viewable else "fas fa-file me-2 text-secondary"),
                            html.Strong(original_name[:20] + "..." if len(original_name) > 20 else original_name)
                        ], className="mb-1"),
                        html.Small([
                            f"{size_mb} MB"
                        ], className="text-muted")
                    ]),
                    dbc.Col([
                        dbc.ButtonGroup([
                            dbc.Button([html.I(className="fas fa-eye")], 
                                     id={"type": "view-btn", "file_name": filename},
                                     color="outline-info", size="sm", 
                                     title="View") if is_viewable else html.Span(),
                            html.A([html.I(className="fas fa-download")], 
                                  href=download_url, className="btn btn-outline-primary btn-sm", 
                                  title="Download")
                        ], size="sm")
                    ], width="auto")
                ])
            ])
        ], className="border-0")
        file_items.append(item)

    return dbc.ListGroup(file_items, flush=True), f"{len(files)} file(s)"


def get_page_content(file_data, page_number):
    if not file_data:
        return None, "File not found"

    lines = file_data['lines']
    
    start_idx = (page_number - 1) * LINES_PER_PAGE
    end_idx = min(start_idx + LINES_PER_PAGE, len(lines))
    
    page_lines = lines[start_idx:end_idx]
    
    return {
        'lines': page_lines,
        'start_line': start_idx + 1,
        'end_line': end_idx,
        'total_lines': len(lines),
        'page_number': page_number,
        'total_pages': file_data['total_pages']
    }, None

def reset_page_data():
    return {'page': 1, 'timestamp': datetime.now().isoformat()}

# FILE VIEW
@callback(
    [Output('file-content', 'children'),
     Output('pagination-controls', 'children'),
     Output('current-file-store', 'data'),
     Output('current-page-store', 'data'),
     Output('notes-info', 'children'),
     Output('notes-area', 'value'),
     Output('auto-save-timer', 'disabled'),
     Output('pagination-trigger-store', 'data', allow_duplicate=True),
     ]
     ,
    [Input({'type': 'view-btn', 'file_name': ALL}, 'n_clicks'),
     State("current-project-store", "data"),
     ],
    prevent_initial_call=True
)
def view_file(n_clicks_list, project_data):
    if not any(n_clicks_list):
        return "Select a file to view", "", None, 1, "", "", True, dash.no_update
    
    if not project_data or not project_data.get("project_id"):
        return "Select a file to view", "", None, 1, "", "", True, dash.no_update
    
    project_id = project_data["project_id"]
    user_id = project_data.get("user_id")
    triggered = ctx.triggered[0]
    if triggered["value"]:
        file_name = json.loads(triggered["prop_id"].split(".n_clicks")[0])["file_name"]
        filename, filepath, original_name, file_size, _ = dbm.get_project_file_info(project_id, file_name)
        if not filename or not filepath or not os.path.exists(filepath):
            return dbc.Alert("File not found", color="danger"), "Select a file to view", "", None, 1, "", "", True
        
        # Load file content
        with open(filepath, 'r', errors='ignore') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        total_pages = (total_lines // LINES_PER_PAGE) + (1 if total_lines % LINES_PER_PAGE > 0 else 0)
        
        file_data = {
            'filename': original_name,
            'file_size_mb': round(file_size / (1024 * 1024), 2) if file_size else 0,
            'lines': lines,
            'total_lines': total_lines,
            'total_pages': total_pages
        }

        # Load notes if exist
        project_dir = Path(f'{UPLOAD_DIRECTORY}/{user_id}/{project_id}')
        notes_file_path = project_dir / "notes.txt"
        
        if file_data:
            """
            # Header
            header = dbc.Alert([
                html.H5(file_data['filename']),
                html.P(f"Size: {file_data['file_size_mb']:.2f}MB | Lines: {file_data['total_lines']:,}")
            ], color="info")
            """
            # Content (Page 1)
            page_content, _ = get_page_content(file_data, 1)
            content = html.Pre('\n'.join(page_content['lines']), style=CODE_STYLE)
            # Pagination
            if file_data['total_pages'] > 1:
                pagination = html.Div([
                    html.P(f"Page 1 of {file_data['total_pages']}", 
                          className="text-center small", id="page-info"),
                    dbc.Pagination(
                        max_value=file_data['total_pages'],
                        active_page=1,
                        size="sm",
                        id="file-paginator",
                        fully_expanded=False,
                        previous_next=True,
                        first_last=True,
                        className="d-flex justify-content-center mt-2"
                    )
                ], className="text-center")
            else:
                pagination = html.Div([
                    html.P("Single page file", className="text-center small text-muted")
                ])
            
            # Notes
            if notes_file_path.exists():
                with open(notes_file_path, 'r') as f:
                    note_content = f.read()
            else:
                note_content = ""

            notes_info = html.Small(f"File: {file_data['filename']}", className="text-muted")
            
            return content, pagination, file_name, 1, notes_info, note_content, False, reset_page_data()
    
    return "Select a file to view", "", None, 1, "", "", True, dash.no_update

# PAGINATION CALLBACK - Now works with suppress_callback_exceptions=True
@callback(
    Output('pagination-trigger-store', 'data'),
    [Input('file-paginator', 'active_page')],
    prevent_initial_call=True
)
def handle_pagination_click(active_page):
    if active_page:
        return {'page': active_page, 'timestamp': datetime.now().isoformat()}
    return dash.no_update

# CONTENT UPDATE CALLBACK
@callback(
    [Output('file-content', 'children', allow_duplicate=True),
     Output('current-page-store', 'data', allow_duplicate=True),
     Output('page-info', 'children')],
    [Input('pagination-trigger-store', 'data')],
    [State('current-file-store', 'data'),
     State("current-project-store", "data"),
     ],
    prevent_initial_call=True
)
def update_file_content(pagination_data, file_name, project_data):
    if not pagination_data or not project_data or not file_name:
        return dash.no_update, dash.no_update, dash.no_update
    
    page = pagination_data.get('page', 1)
    #print("page", page)
    #print("file id",file_name)
    project_id = project_data["project_id"]
    
    filename, filepath, original_name, file_size, _ = dbm.get_project_file_info(project_id, file_name)
    if not filename or not filepath or not os.path.exists(filepath):
        return dbc.Alert("File not found", color="danger"), dash.no_update, dash.no_update
    
    # Load file content
    with open(filepath, 'r', errors='ignore') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    total_pages = (total_lines // LINES_PER_PAGE) + (1 if total_lines % LINES_PER_PAGE > 0 else 0)
    
    file_data = {
        'filename': original_name,
        'file_size_mb': round(file_size / (1024 * 1024), 2) if file_size else 0,
        'lines': lines,
        'total_lines': total_lines,
        'total_pages': total_pages
    }
    page_content, _ = get_page_content(file_data, page)
    if page_content:
        content = html.Pre('\n'.join(page_content['lines']), style=CODE_STYLE)
        page_info = f"Page {page} of {file_data['total_pages']}" if file_data else f"Page {page}"
        
        return content, page, page_info
    
    return dash.no_update, dash.no_update, dash.no_update

# NOTES AUTO-SAVE
@callback(
    [Output('save-status', 'children'),
     Output('char-count', 'children')],
    [Input('auto-save-timer', 'n_intervals'),
     Input('notes-area', 'value'),
     Input("current-project-store", "data")],
    prevent_initial_call=True
)
def auto_save_notes(n_intervals, note_content, project_data):
    if project_data and note_content is not None:
        project_id = project_data.get("project_id")
        user_id = project_data.get("user_id")
        project_dir = Path(f'{UPLOAD_DIRECTORY}/{user_id}/{project_id}')
        notes_file_path = project_dir / "notes.txt"

        with open(notes_file_path, 'w') as f:
            f.write(note_content)
        return "✓ Saved", f"{len(note_content)} chars"
    return "", "0 chars"


def search_file(file_id, pattern):
    if file_id not in file_storage:
        return []
    
    file_data = file_storage[file_id]
    matches = []
    
    try:
        regex = re.compile(pattern, re.IGNORECASE)
        for line_num, line in enumerate(file_data['lines'], 1):
            if regex.search(line):
                matches.append({
                    'line_number': line_num,
                    'line_content': line,
                    'page_number': math.ceil(line_num / LINES_PER_PAGE)
                })
    except:
        return []
    
    return matches

# SEARCH
@callback(
    [Output('search-results', 'children'),
     Output('search-input', 'value')],
    [Input('search-btn', 'n_clicks'),
     Input('btn-error', 'n_clicks'),
     Input('btn-warn', 'n_clicks'), 
     Input('btn-ip', 'n_clicks'),
     Input('btn-time', 'n_clicks')],
    [State('search-input', 'value'),
     State('current-file-store', 'data')],
    prevent_initial_call=True
)
def handle_search(search_clicks, error_clicks, warn_clicks, ip_clicks, time_clicks, 
                 search_pattern, file_id):
    ctx = dash.callback_context
    if not file_id:
        return dbc.Alert("Select a file first", color="info"), dash.no_update
    
    triggered = ctx.triggered_id
    
    # Quick patterns
    patterns = {
        'btn-error': r'\b(ERROR|FATAL|CRITICAL|FAIL)\b',
        'btn-warn': r'\b(WARNING|WARN|ALERT)\b',
        'btn-ip': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        'btn-time': r'\b\d{2}:\d{2}:\d{2}\b'
    }
    
    if triggered in patterns:
        search_pattern = patterns[triggered]
    
    if not search_pattern:
        return "", dash.no_update
    
    matches = search_file(file_id, search_pattern)
    
    if not matches:
        return dbc.Alert("No matches found", color="warning"), search_pattern
    
    results = []
    for match in matches[:15]:
        results.append(
            dbc.Card([
                dbc.CardBody([
                    html.H6(f"Line {match['line_number']} (Page {match['page_number']})", className="small"),
                    html.Pre(match['line_content'][:200] + ("..." if len(match['line_content']) > 200 else ""), 
                            style={'font-size': '11px', 'background': '#f8f9fa', 'padding': '5px'})
                ])
            ], className="mb-2")
        )
    
    return html.Div([
        html.H6(f"Found {len(matches)} matches"),
        html.Div(results, style={'max-height': '300px', 'overflow-y': 'auto'})
    ]), search_pattern

# COLLAPSE TOGGLES
@callback(
    [Output("upload-collapse", "is_open"), Output("upload-icon", "className")],
    [Input("toggle-upload", "n_clicks")], [State("upload-collapse", "is_open")]
)
def toggle_upload(n, is_open):
    if n:
        return not is_open, f"fas fa-chevron-{'right' if is_open else 'down'} me-2"
    return is_open, "fas fa-chevron-down me-2"

@callback(
    [Output("main-collapse", "is_open"), Output("main-icon", "className")],
    [Input("toggle-main", "n_clicks")], [State("main-collapse", "is_open")]
)
def toggle_main(n, is_open):
    if n:
        return not is_open, f"fas fa-chevron-{'right' if is_open else 'down'} me-2"
    return is_open, "fas fa-chevron-down me-2"

@callback(
    [Output("content-collapse", "is_open"), Output("content-icon", "className")],
    [Input("toggle-content", "n_clicks")], [State("content-collapse", "is_open")]
)
def toggle_content(n, is_open):
    if n:
        return not is_open, f"fas fa-chevron-{'right' if is_open else 'down'} me-2"
    return is_open, "fas fa-chevron-down me-2"

@callback(
    [Output("search-view-collapse", "is_open"), Output("search-view-icon", "className")],
    [Input("toggle-search-view", "n_clicks")], [State("search-view-collapse", "is_open")]
)
def toggle_search_view(n, is_open):
    if n:
        return not is_open, f"fas fa-chevron-{'right' if is_open else 'down'} me-2"
    return is_open, "fas fa-chevron-down me-2"