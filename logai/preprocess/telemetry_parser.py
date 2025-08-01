import re
import os
import glob
from logai.utils.constants import TELEMETRY_PROFILES, MERGED_LOGS_DIRECTORY
from logai.utils import json_helper
import pandas as pd
from enum import Enum

class DML(str, Enum):
    TIME = ".Time"
    
    MEM_AVAILABLE = ".meminfoavailable_split"
    MEM_CACHED = ".cachedMem_split"
    MEM_FREE = ".flash_usage_nvram_free_split"
    
    # CPU
    CPU_TEMP = ".cpu_temp_split"
    CPU_USAGE = ".CPUUsage"

    # Device Info
    MAC_ADDRESS = ".mac"
    VER = ".Version"
    PROD_CLS = ".ProductClass"

    SERIAL_NUMBER = ".SerialNumber"
    SW_VERSION = ".Version"
    HW_VERSION = ".hardwareversion"
    MODEL_NAME = ".ModelName"
    MANUFACTURER = ".manufacturer"
    EROUTER = ".erouterIpv4"

    # device status
    WAN_MODE = ".wan_access_mode_split"
    RADIO1_EN = ".wifi_radio_1_enable"
    RADIO2_EN = ".wifi_radio_2_enable"
    AP1_EN = ".wifi_accesspoint_1_status"
    AP2_EN = ".wifi_accesspoint_2_status"
    SSID1 = ".wifi_ssid_1_ssid"
    SSID2 = ".wifi_ssid_2_ssid"
    AIETIES_EDGE = ".airties_edge_enable"
    
    # WAN Sts
    WAN_BYTES_RCVD = ".wan_bytesReceived"
    WAN_BYTES_SENT = ".wan_bytesSent"
    WAN_PKT_RCVD = ".wan_packetsReceived"
    WAN_PKT_SENT = ".wan_packetsSent"

    # SSID Stats
    SSID1_PKT_SENT = ".wifi_ssid_1_stats_packetssent"
    SSID1_PKT_RCVD = ".wifi_ssid_1_stats_packetsreceived"
    SSID1_BYTE_SENT = ".wifi_ssid_1_stats_bytessent"
    SSID1_BYTE_RCVD = ".wifi_ssid_1_stats_bytesreceived"
    SSID1_ERROR_SENT = ".wifi_ssid_1_stats_errorssent"
    SSID1_ERROR_RCVD = ".wifi_ssid_1_stats_errorsreceived"

class Telemetry2Parser:
    """
    Implementation of file data loader, reading log record objects from local files.
    """

    def __init__(self):
        self.log_prefix_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} [^ ]+ T\d\.\w+ \[tid=\d+\] ?", re.MULTILINE)
        self.filename = "telemetry2_0"
        self.file_path = None
        self.telemetry_report = pd.DataFrame()
        self.telemetry_path = TELEMETRY_PROFILES

        if not os.path.exists(self.telemetry_path):
            os.makedirs(self.telemetry_path, exist_ok=True)

    def _check_telemetry_file(self):
        for fname in os.listdir(MERGED_LOGS_DIRECTORY):
            if self.filename in fname:
                self.file_path = os.path.join(MERGED_LOGS_DIRECTORY, fname)
                #print("fle path ", self.file_path)
        
        if self.file_path is not None and os.path.exists(self.file_path):
            return True
        else:
            return False
        
    def extract_telemetry_reports(self):

        if not self._check_telemetry_file():
            #print("return")
            return

        inside_json = False
        open_braces = 0
        json_buffer = ""
        json_blocks = []
        
        with open(self.file_path, "r") as infile:
            for line in infile:
                # Remove log prefixes from line (works anywhere in the line)
                clean_line = self.log_prefix_pattern.sub("", line)
        
                # If not inside a JSON block, look for the beginning
                if not inside_json:
                    brace_pos = clean_line.find("{")
                    if brace_pos != -1:
                        inside_json = True
                        json_buffer = clean_line[brace_pos:]
                        open_braces = json_buffer.count("{") - json_buffer.count("}")
                        if open_braces == 0:
                            json_blocks.append(json_buffer.strip())
                            inside_json = False
                            json_buffer = ""
                else:
                    json_buffer += clean_line
                    open_braces += clean_line.count("{") - clean_line.count("}")
                    if open_braces == 0:
                        json_blocks.append(json_buffer.strip())
                        inside_json = False
                        json_buffer = ""
        
        #print(f"Found {len(json_blocks)} JSON blocks.")
        
        for idx, json_str in enumerate(json_blocks, 1):
            # Remove everything after the last closing '}]}' (or '}}'), plus whitespace and percent
            # Prefer to anchor on '}]}' for your Report use case
            m = re.search(r'(.*\}\]\})', json_str, re.DOTALL)
            if m:
                json_str = m.group(1)
            else:
                # Fallback: Remove trailing percent and whitespace
                json_str = re.sub(r'[%\s]+$', '', json_str)
            outname = f"Telemetry2_report_{idx}.json"
            out_path = os.path.join(self.telemetry_path, outname)
            with open(out_path, "w") as fout:
                fout.write(json_str)
            #print(f"Saved: {outname}")

    def get_timestamp(self):
        data = self.telemetry_report

        if data.empty:
            return False
        
        col_time = DML.TIME
        matching_columns = [col for col in data.columns if col_time.lower() in col.lower()]
        
        timestamp = pd.to_datetime(
                                    self.telemetry_report[matching_columns[0]],
                                    format="%Y-%m-%d %H:%M:%S",
                                )
        #print("TimeStamp", timestamp)
        return timestamp
    
    def get_column_name(self, value):
        data = self.telemetry_report
        
        if self.telemetry_report.empty:
            print("Telemetry Report Empty!")
            return None
        else:
            matching_columns = [col for col in data.columns if value.lower() in col.lower()]
            return matching_columns[0]

    def get_telemetry_col(self,value):
        data = self.telemetry_report

        if self.telemetry_report.empty:
            print("Telemetry Report Empty!")
            return None
        else:
            matching_columns = [col for col in data.columns if value.lower() in col.lower()]
            if len(matching_columns):
                return data[matching_columns[0]]
            else:
                print("Column not Found!", value)
                return None

    def get_telemetry_value(self, value, index=0):
        data = self.telemetry_report
        
        if self.telemetry_report.empty:
            print("Telemetry Report Empty!")
            return None
        else:
            matching_columns = [col for col in data.columns if value.lower() in col.lower()]
            #print(matching_columns)
            if len(matching_columns):
                time_col = self.get_column_name(DML.TIME)
                latest = data.sort_values(time_col).iloc[-1]
                return latest[matching_columns[index]]
            else:
                print("Column not Found!", value)
                return None

    def start_processing(self):
        telemetry_report = pd.DataFrame()

        DATA_LIST = []
        # ---------- Load & prep once at start (or via Upload component) ----------
        for fname in glob.glob(TELEMETRY_PROFILES + "/*.json"):
            RAW = json_helper.load_json(fname)
            if RAW is not None:
                data = json_helper.json_to_df(RAW)
                DATA_LIST.append(data)

        telemetry_report = pd.concat(DATA_LIST)
        excel_path = os.path.join(TELEMETRY_PROFILES, "Telemetry2_report.xlsx")
        try:
            with pd.ExcelWriter(excel_path) as writer:
                telemetry_report.to_excel(writer)
        except Exception as e:
            print("Excepton occured ", e)

        #print(telemetry_report.columns)
        self.telemetry_report = telemetry_report

    def telemetry_report(self):
        return self.telemetry_report