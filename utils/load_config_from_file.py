import os
from pathlib import Path

import yaml
from dotenv import load_dotenv


def load_cfg(cfg_path: str) -> dict:
    load_dotenv()
    raw = Path(cfg_path).read_text()
    expanded = os.path.expandvars(raw)
    cfg = yaml.safe_load(expanded)
    
    # Auto-switch to Docker internal endpoints if running inside Airflow
    if os.environ.get("AIRFLOW_CTX_DAG_ID"):
        if "datalake" in cfg and "endpoint_docker" in cfg["datalake"]:
            cfg["datalake"]["endpoint"] = cfg["datalake"]["endpoint_docker"]
        if "dwh" in cfg:
            if "host_docker" in cfg["dwh"]:
                cfg["dwh"]["host"] = cfg["dwh"]["host_docker"]
            if "port_docker" in cfg["dwh"]:
                cfg["dwh"]["port"] = cfg["dwh"]["port_docker"]
        if "stream" in cfg and "kafka_bootstrap_servers_docker" in cfg["stream"]:
            cfg["stream"]["kafka_bootstrap_servers"] = cfg["stream"]["kafka_bootstrap_servers_docker"]
            
    return cfg
