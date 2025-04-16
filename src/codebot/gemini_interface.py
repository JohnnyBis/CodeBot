import google.generativeai as genai
import logging
import time
from .utils.utils import load_api_key
from .exceptions import LLMInteractionError

class GeminiInterface:
    """Handles interactions with the Google Gemini API."""

    def __init__(self, config):
        """
        Initializes the Gemini interface.

        Args:
            config (dict): Configuration dictionary, expecting 'llm' key for model name etc.

        Raises:
            LLMInteractionError: If API key is missing or configuration fails.
        """
        self.api_key = load_api_key()

        if not self.api_key:
            raise LLMInteractionError("Could not find Gemini API key. Set it in the .env file.")

        try:
            genai.configure(api_key=self.api_key)

            llm_config = config.get('llm', {})
            self.model_name = llm_config.get('model_name', 'gemini-1.5-flash-latest')

            self.model = genai.GenerativeModel(
                self.model_name,
            )

            logging.debug(f"Initialized Gemini with model: {self.model_name}")

        except Exception as e:
            logging.error(f"Failed to configure Gemini API: {e}")
            raise LLMInteractionError(f"Failed to configure Gemini API: {e}") from e


    def query(self, prompt: str, retry_attempts: int = 3, delay: int = 5) -> str:
        """
        Sends a prompt to the Gemini API and returns the response text.

        Args:
            prompt (str): The prompt to send to the LLM.
            retry_attempts (int): Maximum number of retry attempts on failure.
            delay (int): Initial delay in seconds between retries (uses exponential backoff).

        Returns:
            str: The text content of the LLM's response.

        Raises:
            LLMInteractionError: If the prompt is empty or the API call fails.
        """
        if not prompt or not isinstance(prompt, str):
            logging.error("LLM query attempted with invalid prompt.")
            raise LLMInteractionError("Cannot query LLM: Invalid or empty prompt provided.")

        try:
            response = self.model.generate_content(prompt)

            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason

                raise LLMInteractionError(f"Prompt blocked by API. Reason: {block_reason}")

            # Get response content
            if hasattr(response, 'text') and isinstance(response.text, str):
                return response.text
            
            if response.parts:
                result_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
                if result_text:
                    return result_text
                
            raise LLMInteractionError("Response format was unexpected.")
        
        except Exception as e:
            raise LLMInteractionError(f"Error querying Gemini API: {e}")