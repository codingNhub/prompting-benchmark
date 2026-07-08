# Loads and validates YAML config files. Sets global random seed. Returns config object.
# Loads and validates YAML config files. Sets global random seed. Returns config object.

import os
import random
import yaml


def load_config(config_path="configs/config.yaml"):
    # Check if config file exists
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Config file not found: {config_path}\n"
            f"Copy configs/config_template.yaml to configs/config.yaml "
            f"and add your Groq API key."
        )

    # Load the YAML file
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Validate API key exists and is not the placeholder
    api_key = config.get("api", {}).get("groq_key", "")
    if not api_key or api_key == "YOUR_GROQ_KEY_HERE":
        raise ValueError(
            "Groq API key not set in configs/config.yaml\n"
            "Add your real Groq API key to the groq_key field."
        )

    # Set global random seed for reproducibility
    seed = config.get("experiment", {}).get("random_seed", 42)
    random.seed(seed)

    print(f"Config loaded successfully. Random seed: {seed}")
    return config