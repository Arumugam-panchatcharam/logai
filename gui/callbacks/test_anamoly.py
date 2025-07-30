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
from logai.analysis.anomaly_detector import AnomalyDetectionConfig
from logai.algorithms.anomaly_detection_algo.one_class_svm import OneClassSVMDetector, OneClassSVMParams
from logai.applications.log_anomaly_detection import LogAnomalyDetection
from logai.applications.application_interfaces import WorkFlowConfig
from logai.information_extraction.categorical_encoder import CategoricalEncoderConfig
from logai.information_extraction.log_vectorizer import VectorizerConfig
from gui.demo.log_anomaly import LogAnomaly

log_anomaly_demo = LogAnomaly()

def test_parse():
    file_manager = FileManager()
    config_json = file_manager.load_config("WiFilog.txt")
    print(config_json, flush=True)
    if config_json is not None:
        config = WorkFlowConfig.from_dict(config_json)

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
    #workflow_config = WorkFlowConfig.from_dict(config)

    #OneClassSVMDetector(OneClassSVMParams())
    #config.anomaly_detection_config.
    #OneClassSVMDetector.
    #config.anomaly_detection_config = 
    # Create LogAnomalyDetection Application for given workflow_config
    config.log_vectorizer_config = VectorizerConfig()
    config.log_vectorizer_config.algo_name = "tfidf"

    config.categorical_encoder_config = CategoricalEncoderConfig()
    config.categorical_encoder_config.algo_name = "one_hot_encoder"
    print(config, flush=True)
    app = LogAnomalyDetection(config)

    # Execute App
    app.execute()
    print("Labels \n", app.anomaly_labels)
    print("Labels \n", app.anomaly_results)
    #print("attributes", app.evaluation())
    """
    config.log_vectorizer_config = VectorizerConfig()
    config.log_vectorizer_config.algo_name = "tfidf"

    config.categorical_encoder_config = CategoricalEncoderConfig()
    config.categorical_encoder_config.algo_name = "one_hot_encoder"

    #config.clustering_config = ClusteringConfig()
    #config.clustering_config.algo_name = "DBSCAN"

    interval_map = {0: "1s", 1: "1min", 2: "1h", 3: "1d"}
    freq = interval_map[0]
    config.feature_extractor_config.group_by_time = freq
    config.anomaly_detection_config = AnomalyDetectionConfig(algo_name="logbert")
    config.anomaly_detection_config.algo_name = "logbert"

    log_anomaly_demo.execute_anomaly_detection(config)
    """

if __name__ == "__main__":
    test_parse()