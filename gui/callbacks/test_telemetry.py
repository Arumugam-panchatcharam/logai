import os

from gui.file_manager import FileManager

from logai.preprocess.telemetry_parser import Telemetry2Parser
import pandas as pd

telemetry_parser = Telemetry2Parser()

def create_summary_layout(data=pd.DataFrame()):
    print(data["searchResult.Time"])
    latest = data.sort_values('searchResult.Time').iloc[-1]

def test_parse():
    file_manager = FileManager()
    filename = "telemetry2_0"
    config_json = file_manager.load_config(filename)
    #print(config_json, flush=True)
    telemetry_parser.start_processing()
    data = telemetry_parser.telemetry_report
    create_summary_layout(data)

if __name__ == "__main__":
    test_parse()