import yaml
import logging
from dotenv import load_dotenv
import os
import tiktoken

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

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

# --- Token Counting and Truncation ---
# Using tiktoken as a proxy. Replace if a more direct Gemini tokenizer is available/needed.
try:
    # Using cl100k_base encoding, common for newer OpenAI models, as a reasonable proxy
    tokenizer = tiktoken.get_encoding("cl100k_base")
    logging.debug("Tiktoken tokenizer (cl100k_base) loaded for token estimation.")
except Exception:
    logging.warning("Tiktoken library not found or failed to load. Using basic word count for token estimation (less accurate).")
    tokenizer = None

def count_tokens(text):
    """Estimates token count for the given text."""
    if not text:
        return 0
    if tokenizer:
        try:
            return len(tokenizer.encode(text))
        except Exception as e:
            logging.warning(f"Tiktoken encoding failed: {e}. Falling back to word count.")
            # Fallback if encoding fails for some reason
            return len(text.split())
    else:
        # Very rough fallback: split by spaces and punctuation
        return len(text.split())

def truncate_text(text, max_tokens):
    """Truncates text to approximately max_tokens."""
    if not text or max_tokens <= 0:
        return ""

    if count_tokens(text) <= max_tokens:
        return text

    logging.debug(f"Truncating text to approximately {max_tokens} tokens.")

    if tokenizer:
        try:
            tokens = tokenizer.encode(text)
            truncated_tokens = tokens[:max_tokens]
            # Attempt to decode, handle potential errors if cut mid-character
            try:
                truncated_text = tokenizer.decode(truncated_tokens)
                # Add ellipsis if truncation happened
                return truncated_text + "\n... [truncated]"
            except Exception:
                 # Fallback if decoding fails (e.g., cut in the middle of a multi-byte char)
                 try:
                     # Try decoding slightly fewer tokens
                     safer_tokens = tokens[:max(0, max_tokens - 5)] # Ensure index isn't negative
                     truncated_text = tokenizer.decode(safer_tokens)
                     return truncated_text + "\n... [truncated]"
                 except Exception as decode_err:
                     logging.error(f"Failed to decode truncated tokens even after reducing length: {decode_err}")
                     # Last resort: simple character slice based on average token length
                     avg_chars_per_token = 4
                     max_chars = max_tokens * avg_chars_per_token
                     return text[:max_chars] + "\n... [truncated]"
        except Exception as encode_err:
            logging.error(f"Tiktoken encoding failed during truncation: {encode_err}. Falling back to character limit.")
            # Fallback to character limit if encoding itself fails
            avg_chars_per_token = 4
            max_chars = max_tokens * avg_chars_per_token
            return text[:max_chars] + "\n... [truncated]"

    else:
        # Fallback using word count
        words = text.split()
        truncated_words = words[:max_tokens]
        return " ".join(truncated_words) + "\n... [truncated]"