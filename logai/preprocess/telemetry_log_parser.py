import re
import os
import json
from logai.utils.constants import TELEMETRY_PROFILES, MERGED_LOGS_DIRECTORY

class Telemetry2Parser:
    """
    Implementation of file data loader, reading log record objects from local files.
    """

    def __init__(self):
        self.log_prefix_pattern = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2} [^ ]+ T\d\.\w+ \[tid=\d+\] ?", re.MULTILINE)
        self.filename = "telemetry2_0"
        self.file_path = None
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
            return

        inside_json = False
        open_braces = 0
        json_buffer = ""
        json_blocks = []

        with open(self.file_path, "r") as infile:
            for line in infile:
                clean_line = self.log_prefix_pattern.sub("", line)
                # For every collected line, strip newlines and spaces immediately:
                stripped_line = clean_line.strip().replace('\n', '').replace('\r', '')

                if not inside_json:
                    brace_pos = stripped_line.find("{")
                    if brace_pos != -1:
                        inside_json = True
                        json_buffer = stripped_line[brace_pos:]
                        open_braces = json_buffer.count("{") - json_buffer.count("}")
                        if open_braces == 0:
                            json_blocks.append(json_buffer)
                            inside_json = False
                            json_buffer = ""
                else:
                    json_buffer += stripped_line
                    open_braces += stripped_line.count("{") - stripped_line.count("}")
                    if open_braces == 0:
                        json_blocks.append(json_buffer)
                        inside_json = False
                        json_buffer = ""

        for idx, json_str in enumerate(json_blocks, 1):
            # Optionally use your regex anchor here, else simply output
            m = re.search(r'(.*\}\]\})', json_str, re.DOTALL)
            if m:
                json_str = m.group(1)
            else:
                json_str = re.sub(r'[%\s]+$', '', json_str)

            # No post-processing: the json_str is already single-line
            outname = f"Telemetry2_report_{idx}.json"
            out_path = os.path.join(self.telemetry_path, outname)
            with open(out_path, "w", encoding="utf-8") as fout:
                fout.write(json_str)        
