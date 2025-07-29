#
# Copyright (c) 2023 Salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
#
#
import dash_bootstrap_components as dbc
import dash
from dash import html, Input, Output, State, callback, dash_table
from gui.file_manager import FileManager

@callback(
    Output("file-select", "options"),
    Output("file-select", "value"),
    [
        Input('restore-dropdown-value', 'children'),
        Input("upload-data", "filename"), 
        Input("upload-data", "contents")
     ],
)
def upload_file(_, uploaded_filenames, uploaded_file_contents):
    options = []
    file_manager = FileManager()
    ctx = dash.callback_context
    
    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "upload-data":
            if uploaded_filenames is not None and uploaded_file_contents is not None:
                for name, data in zip(uploaded_filenames, uploaded_file_contents):
                    file_manager.save_file(name, data)
            
                file_manager.process_uploaded_files()
        else:
            pass
            #print("Prop_id", prop_id, flush=True)
    else:
        pass
        #print("UPload file else case", flush=True)

    files = file_manager.list_merged_files()

    for filename in files:
        options.append({"label": filename, "value": filename})

    if len(options) > 0:
        return options, options[0]["label"]
    else:
        return options, ""


"""
@callback(
    Output("file-select", "options"),
    Output("file-select", "value"),
    [Input("log-type-select", "value")],
)
def select_file(dataset_name):
    options = []
    files = file_manager.uploaded_files()
    if dataset_name.lower == "custom":
        for filename in files:
            options.append({"label": filename, "value": filename})
    else:
        for filename in files:
            if dataset_name.lower() in filename.lower():
                options.append({"label": filename, "value": filename})

    if len(options) > 0:
        return options, options[0]["label"]
    else:
        return options, ""


@callback(
    Output("custom-file-setting", "children"),
    [Input("log-type-select", "value")],
)
def custom_file_setting(dataset_name):
    if dataset_name.lower() == "custom":
        return html.Div(
            [
                dbc.Textarea(
                    id="custom-file-config",
                    size="lg",
                    className="mb-5",
                    placeholder="custom file loader config",
                )
            ]
        )
    else:
        return html.Div()
"""