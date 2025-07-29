import os

from logai.applications.application_interfaces import (
    WorkFlowConfig,
)
from gui.demo.log_clustering import Clustering
from gui.file_manager import FileManager

#from logai.applications.auto_log_summarization import AutoLogSummarization
from logai.dataloader.openset_data_loader import (
    FileDataLoader,
)
#from ..pages.utils import create_param_table
from logai.analysis.clustering import ClusteringConfig
from logai.information_extraction.categorical_encoder import CategoricalEncoderConfig
from logai.information_extraction.log_vectorizer import VectorizerConfig

log_clustering = Clustering()

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

    config.log_vectorizer_config = VectorizerConfig()
    config.log_vectorizer_config.algo_name = "tfidf"

    config.categorical_encoder_config = CategoricalEncoderConfig()
    config.categorical_encoder_config.algo_name = "one_hot_encoder"

    config.clustering_config = ClusteringConfig()
    config.clustering_config.algo_name = "DBSCAN"

    log_clustering.execute_clustering(config)
    #print("log pattern", log_pattern_demo)
    print("attributes", log_clustering.get_attributes())


if __name__ == "__main__":
    test_parse()