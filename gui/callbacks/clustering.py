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
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig
import dash
import pandas as pd
from dash import html, Input, Output, State, callback, dash_table
import plotly.express as px

from gui.demo.log_pattern import LogPattern
from gui.demo.log_clustering import Clustering
from gui.file_manager import FileManager
from logai.analysis.clustering import ClusteringConfig
from logai.applications.application_interfaces import WorkFlowConfig
from logai.dataloader.openset_data_loader import OpenSetDataLoaderConfig
from logai.information_extraction.categorical_encoder import CategoricalEncoderConfig
from logai.information_extraction.feature_extractor import FeatureExtractorConfig
from logai.information_extraction.log_parser import LogParserConfig
from logai.information_extraction.log_vectorizer import VectorizerConfig
from logai.preprocess.preprocessor import PreprocessorConfig

from ..pages.utils import create_param_table

log_clustering = Clustering()


def _clustering_config():
    config = WorkFlowConfig(
        open_set_data_loader_config=OpenSetDataLoaderConfig(),
        preprocessor_config=PreprocessorConfig(),
        feature_extractor_config=FeatureExtractorConfig(group_by_time="1s"),
        log_parser_config=LogParserConfig(),
        log_vectorizer_config=VectorizerConfig(),
        categorical_encoder_config=CategoricalEncoderConfig(),
        clustering_config=ClusteringConfig(),
    )
    return config


def create_attribute_component(attributes):
    #print(attributes)
    table = dash_table.DataTable(
        id="cluster-attribute-table",
        data=attributes.iloc[:1].to_dict("records"),
        columns=[
            {"id": c, "name": c, "presentation": "dropdown"} for c in attributes.columns
        ],
        editable=True,
        dropdown={
            c: {"options": [{"label": i, "value": i} for i in attributes[c].unique()]}
            for c in attributes.columns
        },
        style_header_conditional=[{"textAlign": "left"}],
        style_cell_conditional=[{"textAlign": "left"}],
        style_header={
            'backgroundColor': 'rgb(50, 50, 50)',
            'color': 'white'
        },
        style_data={
            'backgroundColor': 'white',
            'color': 'black'
        },
    )

    return html.Div(children=[table, html.Div(id="table-dropdown-container")])


@callback(
    Output("clustering-attribute-options", "children"),
    Output("clustering_exception_modal", "is_open"),
    Output("clustering_exception_modal_content", "children"),
    [
        Input("clustering-btn", "n_clicks"),
        Input("clustering_exception_modal_close", "n_clicks"),
    ],
    [
        #State("log-type-select", "value"),
        #State("attribute-name-options", "value"),
        State("file-select", "value"),
        #State("parsing-algo-select", "value"),
        #State("vectorization-algo-select", "value"),
        #State("categorical-encoder-select", "value"),
        #State("clustering-algo-select", "value"),
        #State("clustering-param-table", "children"),
        #State("clustering-parsing-param-table", "children"),
    ],
)
def click_run(
    btn_click,
    modal_close,
    #log_type,
    #attributes,
    filename,
    #parsing_algo,
    #vectorization_algo,
    #categorical_encoder,
    #clustering_algo,
    #clustering_param_table,
    #parsing_param_table,
):
    ctx = dash.callback_context
    if ctx.triggered:
        prop_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if prop_id == "clustering-btn":
            try:
                file_manager = FileManager()
                config_json = file_manager.load_config(filename)
                #print(config_json, flush=True)
                if config_json is not None:
                    # in log clustering disable anomaly detection
                    config_json['anomaly_detection_config'] = None
                    config = WorkFlowConfig.from_dict(config_json)
                    #print(config, flush=True)

                file_path = os.path.join(file_manager.merged_logs_path, filename)

                config.data_loader_config.filepath = file_path

                config.log_vectorizer_config = VectorizerConfig()
                config.log_vectorizer_config.algo_name = "tfidf"

                config.categorical_encoder_config = CategoricalEncoderConfig()
                config.categorical_encoder_config.algo_name = "one_hot_encoder"

                config.clustering_config = ClusteringConfig()
                config.clustering_config.algo_name = "DBSCAN"

                log_clustering.execute_clustering(config)

                return (
                    create_attribute_component(log_clustering.get_attributes()),
                    False,
                    "",
                )
            except Exception as error:
                return html.Div(), True, str(error)
        elif prop_id == "clustering_exception_modal_close":
            return html.Div(), False, ""
    else:
        return html.Div(), False, ""


@callback(Output("cluster-hist", "figure"), [Input("cluster-attribute-table", "data")])
def update_hist(data):
    res = log_clustering.get_unique_clusters()

    df = pd.DataFrame.from_dict(res, orient="index")
    df.index.name = "Cluster"
    df.columns = ["Size"]
    df["Cluster"] = df.index.values
    return generate_pie_chart(df)


def generate_pie_chart(df):
    fig = px.pie(df, names="Cluster", values="Size")

    return fig


@callback(
    Output("clustering-loglines", "children"), [Input("cluster-hist", "clickData")]
)
def update_logline_list(data):
    if data and len(data) > 0:
        cluster_label = data["points"][0]["label"]
        # return html.Div(str(data['points'][0])) # for debug
        df = log_clustering.get_loglines(cluster_label)

        columns = [{"name": c, "id": c} for c in df.columns]
        return dash_table.DataTable(
            data=df.to_dict("records"),
            columns=columns,
            style_table={"overflowX": "scroll"},
            style_cell={
                "max-width": "1020px",
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
            style_header={
                'backgroundColor': 'rgb(50, 50, 50)',
                'color': 'white'
            },
            style_data={
                'backgroundColor': 'white',
                'color': 'black'
            },
        )
    else:
        return dash_table.DataTable()


@callback(
    Output("clustering-summary", "children"),
    [
        Input("cluster-attribute-table", "data"),
    ],
)
def clustering_summary(data):
    if len(data) == 0:
        return html.Div()

    result_table = log_clustering.result_table

    total_loglines = result_table.shape[0]
    total_num_cluster = len(result_table["cluster_id"].unique())

    return html.Div(
        [
            html.P("Total Number Of Loglines: {}".format(total_loglines)),
            html.P("Total Number Of Log Clusters: {}".format(total_num_cluster)),
        ]
    )


@callback(
    Output("clustering-param-table", "children"),
    Input("clustering-algo-select", "value"),
)
def select_clustering_algorithm(algorithm):
    param_info = log_clustering.get_parameter_info(algorithm)
    param_table = create_param_table(param_info)
    return param_table


@callback(
    Output("clustering-parsing-param-table", "children"),
    Input("parsing-algo-select", "value"),
)
def select_parsing_algorithm(algorithm):
    param_info = LogPattern().get_parameter_info(algorithm)
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
Input("clustering-btn-all", "n_clicks"),
Input("clustering_exception_modal_close", "n_clicks"),
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

    

			
