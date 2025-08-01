#
# Copyright (c) 2023 Salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
#
#
import csv
import logging
import os
import re
import sys
import dash
from flask import app
import pandas as pd
import plotly.express as px
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
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
        State("file-select", "value"),
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
                    # in log summarization disable parsing clustering and anomaly detection
                    config_json['anomaly_detection_config'] = None
                    config_json['clustering_config'] = None
                    config = WorkFlowConfig.from_dict(config_json)
                    #print(config, flush=True)

                file_path = os.path.join(file_manager.merged_logs_path, filename)
                if not os.path.getsize(file_path):
                    raise RuntimeError("File Lenght is Zero!")
                
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


def combine_logs_by_timestamp(input_folder, output_log_path):
    """
    Combines log lines from all files in input_folder.
    Lines with valid timestamps are sorted by timestamp.
    Lines without timestamps are appended at the end.
    """
    timestamp_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
    lines_with_ts = []
    lines_without_ts = []

    for root, _, files in os.walk(input_folder):
        for file in files:
            full_path = os.path.join(root, file)
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        match = timestamp_pattern.match(line)
                        if match:
                            lines_with_ts.append((match.group(), line))
                        else:
                            lines_without_ts.append(line)
            except Exception:
                continue  # Skip unreadable files

    # Sort by timestamp
    lines_with_ts.sort(key=lambda x: x[0])

    # Write sorted + unsorted lines to output
    with open(output_log_path, 'w', encoding='utf-8') as out_file:
        for _, line in lines_with_ts:
            out_file.write(line + "\n")
        for line in lines_without_ts:
            out_file.write(line + "\n")

    return output_log_path


def process_with_drain3(input_log_file, output_csv_path):

    logging.basicConfig(stream=sys.stdout, level=logging.WARNING)

    config = TemplateMinerConfig()
    # Optional: comment out or fix config.load if it causes issues
    print("before config load")
    config.load("./gui/assets/drain3.ini")
    print("after config load")
    config.profiling_enabled = False
    config.snapshot_interval_minutes = 0  # Disable snapshotting
    config.save_snapshot = False
    template_miner = TemplateMiner(config=config)
    

    timestamp_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
    processed = []

    with open(input_log_file, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f, 1):
            line = line.strip()
            if not line: continue
            match = timestamp_pattern.match(line)
            timestamp = match.group() if match else ""
            result = template_miner.add_log_message(line)
            if result:
                processed.append({
                    "timestamp": timestamp,
                    "cluster_id": result["cluster_id"],
                    "template": result["template_mined"],
                    "log": line
                })
            if idx % 1000 == 0:
                print(f"Processed {idx} lines...")
    print(f"Done: processed {len(processed)} lines. Now writing CSV.")

    with open(output_csv_path, 'w', newline='', encoding='utf-8') as cf:
        writer = csv.DictWriter(cf, fieldnames=["timestamp", "cluster_id", "template", "log"])
        writer.writeheader()
        for row in processed:
            writer.writerow(row)

    print("CSV written:", output_csv_path)




@callback(
Output("pattern-graph_total", "figure"),
#Output("status-msg", "children"),
[
Input("pattern-btn-all", "n_clicks"),
Input("pattern_exception_modal_close", "n_clicks"),
],
prevent_initial_call=True
)
def on_run_click(n_clicks, modal_close):
    try:
        file_manager = FileManager()
         # The folder with uploaded logs
        output_log_path = os.path.join(file_manager.merged_logs_path, 'combined.log')  # Combined output log
        output_csv_path = os.path.join(file_manager.merged_logs_path, 'processed.csv') # Drain3 output CSV
        # Step 1: Combine logs or do pre-processing
        print("Combining logs from:", file_manager.merged_logs_path)
        combine_logs_by_timestamp(file_manager.merged_logs_path,output_log_path)# e.g., combine logs

        # Step 2: Run Drain3 or pattern mining
        print("Processing logs with Drain3...")
        process_with_drain3(output_log_path,output_csv_path) # generates "processed.csv"

        # Step 3: Load resulting CSV
        df = pd.read_csv(output_csv_path)
        print("read csv.")
        # Example: Plot count of logs per template
        fig = px.scatter(df, x="cluster_id",title="Log Template Frequency",custom_data=["cluster_id", "template", "log"])
        print("Plotting done.")
        return fig 
    

    except Exception as e:
        return dash.no_update, f"❌ Error: {str(e)}"    
    
@callback(
    Output("cluster-tmp", "children"),
    Input("pattern-graph_total", "clickData"),
    prevent_initial_call=True
    )

def show_cluster_details(clickData):
        if not clickData or "points" not in clickData:
            return "No data selected."
        point = clickData["points"][0]
        # customdata = [cluster_id, template, log]
        if "customdata" in point and point["customdata"]:
            cluster_id, template, log = point["customdata"]
            return html.Div([
                html.H4(f"Cluster ID: {cluster_id}"),
                html.B("Template: "), html.Pre(template, style={"whiteSpace": "pre-wrap"}), html.Br(),
                html.B("Log: "), html.Pre(log, style={"whiteSpace": "pre-wrap"}),
            ], style={'backgroundColor': '#FFFFFF', 'padding': '1em', 'borderRadius': '10px'})
        else:
            return html.Div([
            "No cluster data found in selection.",
            html.Pre(str(point), style={"color": "crimson", "fontSize": "smaller"})
             ])

    

			
