#
# Copyright (c) 2023 Salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
#
#
import os
import dash
import pandas as pd
import plotly.express as px

from dash import html, Input, Output, State, callback, dash_table

from logai.applications.application_interfaces import (
    WorkFlowConfig,
    FeatureExtractorConfig,
    PreprocessorConfig,
    LogParserConfig,
)

from gui.file_manager import FileManager
from gui.demo.log_pattern import LogPattern
from logai.dataloader.openset_data_loader import (
    FileDataLoader,
)
from ..pages.utils import create_param_table

log_pattern_demo = LogPattern()

def _config_sample():
    config = WorkFlowConfig(
        data_loader_config=FileDataLoader(),
        feature_extractor_config=FeatureExtractorConfig(),
        preprocessor_config=PreprocessorConfig(
            custom_delimiters_regex=[":", ",", "=", "\t"]
        ),
        log_parser_config=LogParserConfig(),
    )
    return config


def create_attribute_component(attributes):
    table = dash_table.DataTable(
        id="attribute-table",
        data=[{c: "*" for c in attributes.columns}],
        columns=[
            {"id": c, "name": c, "presentation": "dropdown"} for c in attributes.columns
        ],
        editable=True,
        dropdown={
            c: {
                "options": [{"label": "*", "value": "*"}]
                + [{"label": i, "value": i} for i in attributes[c].unique()]
            }
            for c in attributes.columns
        },
        style_header_conditional=[{"textAlign": "left"}],
        style_cell_conditional=[{"textAlign": "left"}],
    )
    return html.Div(children=[table, html.Div(id="table-dropdown-container")])

"""
@callback(
    Output("attribute-name-options", "options"),
    Output("attribute-name-options", "value"),
    [
        Input(component_id="log-type-select", component_property="value"),
    ],
)
def get_attributes(log_type):
    if log_type.lower() == "custom":
        return [], []

    config = OpenSetDataLoaderConfig(
        dataset_name=log_type,
    )

    data_loader = OpenSetDataLoader(config)
    dl_config = data_loader.dl_config
    attributes = dl_config.dimensions["attributes"]

    if attributes is None:
        return [], []

    options = [{"label": str(c), "value": str(c)} for c in attributes]
    values = [str(c) for c in attributes]
    return options, values
"""

@callback(
    Output("attribute-options", "children"),
    Output("pattern_exception_modal", "is_open"),
    Output("pattern_exception_modal_content", "children"),
    [
        Input("pattern-btn", "n_clicks"),
        Input("pattern_exception_modal_close", "n_clicks"),
    ],
    [
        #State("log-type-select", "value"),
        #State("attribute-name-options", "value"),
        State("file-select", "value"),
        #State("parsing-algo-select", "value"),
        #State("parsing-param-table", "children"),
    ],
)
def click_run(
    btn_click, modal_close, filename
):
    ctx = dash.callback_context
    try:
        if ctx.triggered:
            prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if prop_id == "pattern-btn":
                file_manager = FileManager()
                config_json = file_manager.load_config(filename)
                #print(config_json, flush=True)
                if config_json is not None:
                    config = WorkFlowConfig.from_dict(config_json)
                    #print(config, flush=True)

                file_path = os.path.join(file_manager.merged_logs_path, filename)
                config.data_loader_config.filepath = file_path
                log_pattern_demo.execute_auto_parsing(config)

                return (
                    create_attribute_component(
                        log_pattern_demo.get_attributes()
                    ),
                    False,
                    "",
                )
            elif prop_id == "pattern_exception_modal_close":
                return html.Div(), False, ""
        else:
            return html.Div(), False, ""
    except Exception as error:
        return html.Div(), True, str(error)


@callback(Output("log-patterns", "children"), [Input("summary-scatter", "clickData")])
def update_log_pattern(data):
    if data is not None:
        res = data["points"][0]["customdata"]

        return html.Div(
            children=[html.B(res)],
            style={
                "width": "100 %",
                "display": "in-block",
                "align-items": "left",
                "justify-content": "left",
            },
        )
    else:
        return html.Div()


@callback(
    Output("log-dynamic-lists", "children"), [Input("summary-scatter", "clickData")]
)
def update_dynamic_lists(data):
    if data is not None:
        df = log_pattern_demo.get_dynamic_parameter_list(
            data["points"][0]["customdata"]
        )
        df["values"] = df["values"].apply(lambda x: ", ".join(set(filter(None, x))))
        df = df.rename(
            columns={"position": "Position", "value_counts": "Count", "values": "Value"}
        )
        columns = [{"name": c, "id": c} for c in df.columns]
        return dash_table.DataTable(
            data=df.to_dict("records"),
            columns=columns,
            style_table={"overflowX": "scroll"},
            style_cell={"max-width": "900px", "textAlign": "left"},
            editable=False,
            row_selectable="multi",
            sort_action="native",
            sort_mode="multi",
            column_selectable="single",
        )
    else:
        return dash_table.DataTable()


@callback(
    Output("select-loglines", "children"), [Input("summary-scatter", "clickData")]
)
def update_logline(data):
    if data is not None:
        df = log_pattern_demo.get_log_lines(data["points"][0]["customdata"])
        columns = [{"name": c, "id": c} for c in df.columns]
        return dash_table.DataTable(
            data=df.to_dict("records"),
            columns=columns,
            style_table={"overflowX": "scroll"},
            style_cell={
                "max-width": "900px",
                "textAlign": "left",
            },
            editable=True,
            row_selectable="multi",
            sort_action="native",
            sort_mode="multi",
            column_selectable="single",
            page_action="native",
            page_size=20,
            page_current=0,
        )
    else:
        return dash_table.DataTable()


@callback(
    Output("summary-scatter", "figure"),
    [Input("attribute-table", "data")],
)
def update_summary_graph(data):
    attribute = []
    for c in data:
        for k, v in c.items():
            if not v == "*":
                attribute.append({k: v})

    scatter_df = log_pattern_demo.summary_graph_df(attribute)

    fig = px.bar(
        scatter_df,
        x="order",
        y="counts",
        labels={"order": "log pattern", "counts": "Occurrence (Log Scale)"},
        hover_name=scatter_df.index.values,
    )
    fig.update_traces(customdata=scatter_df.index.values)

    fig.update_yaxes(type="log")

    fig.update_layout(margin={"l": 40, "b": 40, "t": 10, "r": 0}, hovermode="closest")
    return fig


@callback(
    Output("pattern-time-series", "figure"),
    [Input("summary-scatter", "clickData"), Input("time-interval", "value")],
    prevent_initial_call=True,
)
def update_y_timeseries(data, interval):
    #print(data)
    if not data:
        return
    interval_map = {0: "1s", 1: "1min", 2: "1h", 3: "1d"}
    pattern = data["points"][0]["customdata"]
    freq = interval_map[interval]
    result_df = log_pattern_demo.result_table
    dff = result_df[result_df["parsed_logline"] == pattern][
        ["timestamp", "parsed_logline"]
    ]
    #print(dff)
    ts_df = (
        dff[["timestamp", "parsed_logline"]]
        .groupby(pd.Grouper(key="timestamp", freq=freq, offset=0, label="right"))
        .size()
        .reset_index(name="count")
    )

    title = "Trend of Occurrence at Freq({})".format(freq)
    return create_time_series(ts_df, "Linear", title)


def create_time_series(dff, axis_type, title):
    fig = px.scatter(
        dff,
        x="timestamp",
        y="count",
        labels={"count": "Occurrence", "timstamp": "Time"},
        title=title,
    )

    fig.update_traces(mode="lines+markers")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(type="linear" if axis_type == "Linear" else "log")
    fig.update_layout(margin={"l": 20, "b": 30, "r": 10, "t": 30})
    return fig


@callback(
    Output("log-summarization-summary", "children"),
    [
        Input("attribute-table", "data"),
    ],
)
def summary(data):
    if len(data) > 0:
        result_table = log_pattern_demo.result_table
        total_loglines = result_table.shape[0]
        total_log_patterns = len(result_table["parsed_logline"].unique())

        return html.Div(
            [
                html.P("Total Number of Loglines: {}".format(total_loglines)),
                html.P("Total Number of Log Patterns: {}".format(total_log_patterns)),
            ]
        )
    else:
        return html.Div(
            [
                html.P("Total Number of Loglines: "),
                html.P("Total Number of Log Patterns: "),
            ]
        )


@callback(
    Output("parsing-param-table", "children"), Input("parsing-algo-select", "value")
)
def select_parsing_algorithm(algorithm):
    param_info = None
    if log_pattern_demo is not None:
        param_info = log_pattern_demo.get_parameter_info(algorithm)
    param_table = create_param_table(param_info)
    return param_table
