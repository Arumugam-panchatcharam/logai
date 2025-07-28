#
# Copyright (c) 2023 Salesforce.com, inc.
# All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
# For full license text, see the LICENSE file in the repo root or https://opensource.org/licenses/BSD-3-Clause
#
#
import os
import base64
import shutil
import tarfile
import json
from dataclasses import dataclass
from dash import html
from urllib.parse import quote as urlquote

from logai.utils.constants import UPLOAD_DIRECTORY, MERGED_LOGS_DIRECTORY

from typing import List, Optional, Tuple, Dict, Any

@dataclass
class ConfigEntry:
    name: str
    supported_config: str
    supported_files: List[str]

@dataclass
class ConfigIndex:
    supported_files: List[ConfigEntry]

    @staticmethod
    def load_from_file(index_path: str) -> 'ConfigIndex':
        with open(index_path, 'r') as f:
            raw_data = json.load(f)
        entries = [ConfigEntry(**entry) for entry in raw_data.get("supported_files", [])]
        return ConfigIndex(supported_files=entries)

    def find_config_for_file(self, filename: str) -> str:
        filename_base = os.path.basename(filename)

        for entry in self.supported_files:
            for supported_name in entry.supported_files:
                if supported_name.lower() in filename_base.lower():
                    return entry.supported_config
        raise ValueError(f"No config found for file: {filename}")

class FileManager:
    """Processor for handling uploaded files in the application."""
    def __init__(self):
        self.directory = UPLOAD_DIRECTORY
        self.merged_logs_path = MERGED_LOGS_DIRECTORY
        #self.base_directory = path
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)

    # === Save uploaded file to local folder ===
    def save_file(self, name, content):
        content_type, content_string = content.split(',')
        decoded = base64.b64decode(content_string)
        file_path = os.path.join(self.directory, name)
        with open(file_path, "wb") as f:
            f.write(decoded)
    """
    def save_file(self, name, content):
        data = content.encode("utf8").split(b";base64,")[1]
        with open(os.path.join(self.directory, name), "wb") as fp:
            fp.write(base64.decodebytes(data))
    """ 
    def uploaded_files(self):
        files = []
        for filename in os.listdir(self.directory):
            path = os.path.join(self.directory, filename)
            if os.path.isfile(path):
                files.append(filename)
        return files

    def file_download_link(self, filename):
        location = "/download/{}".format(urlquote(filename))
        return html.A(filename, href=location)
    
    def process_uploaded_files(self):
        """Process uploaded files by extracting and merging logs."""
        if not os.path.exists(self.directory):
            raise FileNotFoundError(f"Upload directory '{self.path}' does not exist.")
        
        # Create a temporary directory for extraction
        temp_dir = os.path.join(self.directory, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        for file in os.listdir(self.directory):
            filename = file.lower()
            if filename.endswith(".tgz") or filename.endswith(".tar.gz"):
                src_file = os.path.join(self.directory, file)
                base = file.rsplit('.', 2)[0]
                dest = os.path.join(temp_dir, base)
                os.makedirs(dest, exist_ok=True)
                with tarfile.open(src_file, "r:gz") as tar:
                    tar.extractall(path=dest)
        
        self._merge_files(temp_dir, output_dir=os.path.join(self.directory, "merged_logs"))
        self._clean_temp_files(input_dir=temp_dir)

    def _merge_files(self,temp_dir, output_dir="./merged_logs"):
        os.makedirs(output_dir, exist_ok=True)
        folder_path = temp_dir
        folders = os.listdir(folder_path)
        folders.sort()

        for dirname in folders:
            content = os.path.join(folder_path, dirname)
            dirs = os.listdir(content)
            if len(dirs) == 1:
                for inner_dirname in dirs:
                    in_path = os.path.join(content, inner_dirname)
            else:
                in_path = content

            for in_filename in os.listdir(in_path):
                if (
                    "2023" not in in_filename
                    and "2024" not in in_filename
                    and "2025" not in in_filename
                ):
                    out_filename = in_filename
                else:
                    out_filename = in_filename[19:]
                    if "024-" in out_filename:
                        out_filename = in_filename[37:]
                    if "1_" in out_filename:
                        out_filename = out_filename[2:]
                    if out_filename and out_filename[0] in "0123456789_":
                        out_filename = out_filename[1:]

                out_file = os.path.join(output_dir, out_filename)
                in_file = os.path.join(in_path, in_filename)

                with open(in_file, "rb") as rd, open(out_file, "ab") as wr:
                    #message = "****Merging " + in_file + " **********\n"
                    #wr.write(message.encode("utf-8"))
                    shutil.copyfileobj(rd, wr)

    def _clean_temp_files(self,input_dir):
        for name in os.listdir(input_dir):
            full_path = os.path.join(input_dir, name)
            if os.path.isdir(full_path):
                shutil.rmtree(full_path)
            else:
                os.remove(full_path)
        os.rmdir(input_dir)
        print(f"Cleaned all contents from {input_dir}")

    def list_uploaded_files(self):
        """List all files saved in the uploads folder."""
        try:
            return sorted(os.listdir(self.directory))
        except FileNotFoundError:
            return []

    def list_merged_files(self):
        """List all files saved in the uploads folder."""
        try:
            merged_logs_path = MERGED_LOGS_DIRECTORY
            return sorted(os.listdir(merged_logs_path), reverse=True)
        except FileNotFoundError:
            return []
        
    def load_config(self, filename):

        root_dir = os.path.dirname(os.path.abspath(__file__))
        config_list_path = os.path.join(root_dir, "../configs", "config_list.json")

        if os.path.exists(config_list_path):
            #print(f"Loading config from {config_list_path}")
            self.config_index = ConfigIndex.load_from_file(config_list_path)
            if self.config_index:
                file_config = self.config_index.find_config_for_file(filename)
                self.config_path = os.path.join(root_dir, "../configs", file_config)
                #print("config {}, path {}".format(self.config, self.config_path))
                if os.path.exists(self.config_path):
                    try:
                         with open(self.config_path, 'r') as f:
                            raw_data = json.load(f)
                            return raw_data
                    except json.JSONDecodeError as e:
                        print(f"Error decoding invalid JSON: {e}\n")
                    except Exception as e:
                        print(f"An unexpected error occurred: {e}\n")