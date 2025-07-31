import os
import csv
import re
import sys
from drain3 import TemplateMiner
from drain3.template_miner_config import TemplateMinerConfig

from typing import List, Dict

import pandas as pd
from dataclasses import dataclass

from abc import ABC, abstractmethod

from logai.algorithms.algo_interfaces import ParsingAlgo
from logai.config_interfaces import Config
from logai.algorithms.factory import factory


@dataclass
class Drain3Params(Config):
    """Parameters for Drain Log Parser. 
    For more details on parameters see 
    https://github.com/logpai/Drain3/blob/master/drain3/drain.py.

    :param depth: The depth of tree.
    :param sim_th: The similarity threshold.
    :param max_children: The max number of children nodes.
    :param max_clusters: The max number of clusters.
    :param extra_delimiters: Extra delimiters.
    :param param_str: The wildcard parameter string.
    """
    depth: int = 3
    sim_th: float = 0.4
    max_children: int = 100
    max_clusters: int = None
    extra_delimiters: tuple = ()
    param_str: str = "*"

    @classmethod
    def from_dict(cls, config_dict):
        config = super(Drain3Params, cls).from_dict(config_dict)
        if config.extra_delimiters:
            config.extra_delimiters = tuple(config.extra_delimiters)
        return config

@factory.register("parsing", "drain", Drain3Params)
class Drain_3(ParsingAlgo):
    def __init__(self):
        super().__init__()

    def parse(self, logline: pd.Series) -> pd.Series:
        """Parse method to run log parser on a given log data.

        :param logline: The raw log data to be parsed.
        :returns: The parsed log data.
        """
        self.fit(logline)
        parsed_logline = []
        for line in logline:
            parsed_logline.append(" ".join(self.match(line).log_template_tokens))
        return pd.Series(parsed_logline, index=logline.index)
    
    def parse(self, logline: pd.Series) -> pd.Series:
        drain3_config = TemplateMinerConfig()
        drain3_config.load("./drain3.ini")
        drain3_config.profiling_enabled = False
        processed = []
        template_miner = TemplateMinerConfig(config = drain3_config)

        """
        with open (input_log_file, output_csv_file) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                result = template_miner.add_log_message(line)
                if result:
                    processed.append({
                        "cluster_id": result["cluster_id"],
                        "template" : result["template_mined"],
                        "log" : line
                    })
        with open(output_csv_file,'w',newline='') as cf:
            writer = csv.DictWriter(cf,fieldnames=["cluster_id","template","log"])
            writer.writeheader()
            for row in processed:
                writer.writerow(row)
        """

