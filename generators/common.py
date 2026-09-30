from pathlib import Path
import random

import numpy as np
import yaml


# GridSense project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Central data-generation configuration
CONFIG_PATH = PROJECT_ROOT / "config" / "data_generation.yaml"


def load_config():
    """Load the central data-generation configuration."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def initialize_random_seed(config):
    """Initialize Python and NumPy random generators."""
    seed = config["project"]["random_seed"]

    random.seed(seed)
    np.random.seed(seed)


def create_output_directories(config):
    """Create all configured raw-data directories."""
    output_config = config["output"]

    for key, relative_path in output_config.items():
        if key == "base_path":
            continue

        output_path = PROJECT_ROOT / relative_path
        output_path.mkdir(parents=True, exist_ok=True)


def get_project_root():
    """Return the GridSense project root directory."""
    return PROJECT_ROOT


def get_regions(config):
    """Return the configured list of regions."""
    return config["regions"]