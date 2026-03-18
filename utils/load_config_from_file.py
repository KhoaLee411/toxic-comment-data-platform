import os
import yaml
from dotenv import load_dotenv


def load_cfg(cfg_file):
    """
    Load configuration from a YAML config file and substitute environment variables.
    """
    load_dotenv()  # Load variables from .env if it exists
    
    with open(cfg_file, "r") as f:
        try:
            # Read the file content and expand environment variables
            content = f.read()
            # Use os.path.expandvars to replace ${VAR} or $VAR with environment values
            expanded_content = os.path.expandvars(content)
            cfg = yaml.safe_load(expanded_content)
        except yaml.YAMLError as exc:
            print(f"Error parsing YAML: {exc}")
            return None
        except Exception as e:
            print(f"Error loading config: {e}")
            return None

    return cfg
