#
# Copyright (c) 2023 Salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
#
#
import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, State
from gui.app_instance import app, flask_server

from gui.pages.utils import create_banner
from gui.pages import pattern as pattern_page
from gui.pages import anomaly_detection as anomaly_page
from gui.pages import clustering as clustering_page
from gui.pages import ai_analysis as ai_analysis_page
from gui.callbacks import pattern, anomaly_detection, clustering, utils, ai_analysis
from gui.file_manager import FileManager
from flask import Flask
flask_server = Flask(__name__)

file_manager = FileManager()
file_manager.clean_temp_files()

#server = app.server
#app.config["suppress_callback_exceptions"] = True

file_manager = FileManager()
file_manager.clean_temp_files()

app.layout = dbc.Container(
    [
        dcc.Location(id="url", refresh=False),
        html.Div(id='restore-dropdown-value', style={'display':'none'}),
        dbc.Container(id="page-content", fluid=True),
    ],
    fluid=True,
)


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    if pathname == "/logai/pattern":
        return dbc.Container(
            [dbc.Row(create_banner(app)), pattern_page.layout], fluid=True
        )
    elif pathname == "/logai/anomaly":
        return dbc.Container(
            [dbc.Row(create_banner(app)), anomaly_page.layout], fluid=True
        )
    elif pathname == "/logai/clustering":
        return dbc.Container(
            [dbc.Row(dbc.Col(create_banner(app))), clustering_page.layout], fluid=True
        )
    elif pathname == "/logai/ai_analysis":
        return dbc.Container(
            [dbc.Row(dbc.Col(create_banner(app))), ai_analysis_page.layout], fluid=True
        )
    else:
        return dbc.Container(
            [dbc.Row(dbc.Col(create_banner(app))), pattern_page.layout], fluid=True
        )


if __name__ == "__main__":
    #import nltk
    #nltk.download('punkt_tab')
    app.run(debug=True)
