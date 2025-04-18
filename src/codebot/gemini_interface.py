import google.generativeai as genai
import logging
from .utils.utils import load_api_key
from .exceptions import LLMInteractionError

class GeminiInterface:
    """Handles interactions with the Google Gemini API."""

    def __init__(self, config):
        """
        Initializes the Gemini interface.
        """
        self.api_key = load_api_key()

        if not self.api_key:
            raise LLMInteractionError("Could not find Gemini API key. Please set it in the .env file.")

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


    def query(self, prompt: str) -> str:
        """
        Sends a prompt to the Gemini API and returns the response text.
        """
        if not prompt or not isinstance(prompt, str):
            logging.error("Invalid or empty prompt provided.")
            raise LLMInteractionError("Unable to query LLM, invalid or empty prompt provided.")

        try:
            response = self.model.generate_content(prompt)

            if response.prompt_feedback and response.prompt_feedback.block_reason:
                block_reason = response.prompt_feedback.block_reason

                raise LLMInteractionError(f"Prompt blocked by API: {block_reason}")

            # Get response content
            if hasattr(response, 'text') and isinstance(response.text, str):
                return response.text
            
            if response.parts:
                result_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
                if result_text:
                    return result_text
                
            raise LLMInteractionError("Response format was unexpected.")
        
        except Exception as e:
            raise LLMInteractionError(f"Unable to query Gemini API: {e}")