import os

from gui.file_manager import FileManager

from logai.preprocess.telemetry_parser import Telemetry2Parser
import pandas as pd
from logai.preprocess.telemetry_parser import DML
telemetry_parser = Telemetry2Parser()

def create_summary_layout(data=pd.DataFrame()):
    if data.empty:
        return
    print(data["searchResult.Time"])
    latest = data.sort_values('searchResult.Time').iloc[-1]
def create_table(data=pd.DataFrame()):
    if data.empty:
        return
    
    time = telemetry_parser.get_timestamp()
    ccsp_mem_usage_raw = telemetry_parser.get_telemetry_col(DML.CCSP_MEM_USAGE_SPLIT)
    data_table = []
    result_df = pd.DataFrame()
    for process_data, t in zip(ccsp_mem_usage_raw, time):
        if pd.isna(process_data):
            continue
        #pdata = {'TimeStamp': t}
        parsed_data = telemetry_parser.key_value_split(process_data, t)
        #print(parsed_data)
        #pdata.append(parsed_data)
        #parsed_data.append({'TimeStamp': t})
        #data_table.append(parsed_data)
        result_df = pd.concat([result_df, parsed_data], ignore_index=True)
    
    #print(result_df)
    print(result_df.sort_values(['NAME', 'TimeStamp']))

def test_parse():
    file_manager = FileManager()
    filename = "telemetry2_0"
    #config_json = file_manager.load_config(filename)
    telemetry_parser.extract_telemetry_reports()
    #print(config_json, flush=True)
    telemetry_parser.start_processing()
    data = telemetry_parser.telemetry_report
    #print(data)
    #create_summary_layout(data)
    create_table(data)

if __name__ == "__main__":
    test_parse()