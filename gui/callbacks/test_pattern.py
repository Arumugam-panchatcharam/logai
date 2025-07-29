import os

from logai.applications.application_interfaces import (
    WorkFlowConfig,
)

from gui.file_manager import FileManager
from gui.demo.log_pattern import LogPattern
#from logai.applications.auto_log_summarization import AutoLogSummarization
from logai.dataloader.openset_data_loader import (
    FileDataLoader,
)
#from ..pages.utils import create_param_table

log_pattern_demo = LogPattern()

def test_parse():
    file_manager = FileManager()
    config_json = file_manager.load_config("WiFilog.txt")
    print(config_json, flush=True)
    if config_json is not None:
        config = WorkFlowConfig.from_dict(config_json)
        print(config, flush=True)

    file_path = os.path.join(file_manager.merged_logs_path, "WiFilog.txt")
    """
    params = log_pattern_demo.parse_parameters(
        param_info=log_pattern_demo.get_parameter_info(parsing_algo),
        params={
            p["Parameter"]: p["Value"]
            for p in param_table["props"]["data"]
            if p["Parameter"]
        },
    )
    """
    config.data_loader_config.filepath = file_path
    log_pattern_demo.execute_auto_parsing(config)
    #print("log pattern", log_pattern_demo)
    print("attributes", log_pattern_demo.get_attributes())


if __name__ == "__main__":
    test_parse()