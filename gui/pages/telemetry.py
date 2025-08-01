#
# Copyright (c) 2023 Salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
#
#
import dash_bootstrap_components as dbc
from dash import dcc, html

from .utils import (
    create_modal,
    create_description_card,
    create_upload_file_layout,
    create_run_button
)


def create_control_card():
    return html.Div(
        id="control-card",
        children=[
            create_upload_file_layout(),
            #create_file_setting_layout(),
            html.Hr(),
            create_run_button("telemetry-btn"),
            create_modal(
                modal_id="telemetry_exception_modal",
                header="An Exception Occurred",
                content="An exception occurred. Please click OK to continue.",
                content_id="telemetry_exception_modal_content",
                button_id="telemetry_exception_modal_close",
            ),
        ],
    )

def create_timeseries_grapy_layout():
    return html.Div(
        children=[
            dcc.Graph(id="telemetry-time-series"),
        ],
        # style={
        #     'display': 'inline-block',
        #     'width': '59%'
        # },
    )


def create_telemetry_layout():
    return dbc.Row(
        [
            # Left column
            dbc.Col(
                html.Div(
                    [
                        create_description_card(),
                        create_control_card(),
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
                        html.H4("Telemetry Summarizaton"),
                        html.Hr(),
                        dbc.Row(
                            [
                                dbc.Col(dbc.Card([
                                    dbc.CardHeader("Device Info"),
                                    dbc.CardBody(id="dev-summary-card", children=html.Div("Click 'Run' to load summary."))
                                ]), width=4),
                                dbc.Col(dbc.Card([
                                    dbc.CardHeader("Device Status"),
                                    dbc.CardBody(id="dev-status-card", children=html.Div("Click 'Run' to load summary."))
                                ]), width=4),
                            ],
                        ),
                        html.Hr(),
                        dbc.Row([
                            dbc.Col(dbc.Card([
                                    dbc.CardHeader("Memory Split"),
                                    dbc.CardBody(id="mem-chart-card", children=html.Div("Click 'Run' to load chart."))
                                ]), width=6),
                            dbc.Col(dbc.Card([
                                    dbc.CardHeader("Network Stats"),
                                    dbc.CardBody(id="network-stat-chart-card", children=html.Div("Click 'Run' to load chart."))
                                ]), width=6),
                        ]),
                        html.Hr(),
                        dbc.Row([
                            dbc.Col(dbc.Card([
                                    dbc.CardHeader("CPU Usage vs CPU Temp"),
                                    dbc.CardBody(id="cpu-chart-card", children=html.Div("Click 'Run' to load chart."))
                                ]), width=6),
                            dbc.Col(dbc.Card([
                                    dbc.CardHeader("Radio Stats"),
                                    dbc.CardBody(id="radio-stat-chart-card", children=html.Div("Click 'Run' to load chart."))
                                ]), width=6),
                        ])
                    ]
                )
            ),
        ]
    )


layout = create_telemetry_layout()
