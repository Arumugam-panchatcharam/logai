import re
import os

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