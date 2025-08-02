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
