import yaml
import logging
from dotenv import load_dotenv
import os

def load_config(path="config.yaml"):
    """Loads YAML configuration file."""
    try:
        with open(path, 'r') as f:
            config = yaml.safe_load(f)
            return config
    except Exception as e:
        logging.error(f"Unexpected error loading configuration from {path}: {e}")
        return None

def load_api_key():
    """Loads "GEMINI_API_KEY" from .env file."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logging.error("API key not found in .env file.")
    return api_key

def get_file_structure(code_files: dict) -> list:
    """
    Static function.
    Generates a simple list of file paths from the loaded code files.
    """
    if not code_files:
        return []
    return list(code_files.keys())