import logging
from .gemini_interface import GeminiInterface
from .prompt_manager import PromptManager
from .exceptions import ContextSelectionError, LLMInteractionError

class ContextSelector:
    """
    Selects relevant code context for a given query using an LLM-based approach.
    """

    def __init__(self, config: dict, gemini_interface: GeminiInterface, prompt_manager: PromptManager):
        """
        Initializes the ContextSelector.
        """
        self.repo_config = config.get('repository', {})
        self.llm_config = config.get('llm', {})
        self.llm = gemini_interface
        self.prompter = prompt_manager

        # Configurations
        self.max_context_files = self.repo_config.get('max_context_files', 6)
        self.max_total_context_tokens = self.llm_config.get('max_context_tokens', 8000)

    def select_relevant_files(self, query: str, file_structure: list) -> list:
        """
        Uses Gemini to identify relevant files based on names and the query.
        """
        if not file_structure:
            logging.warning("No file structure provided for context selection. Cannot select files.")
            return []
        
        selection_prompt = self.prompter.format_selection_prompt(query, file_structure)

        try:
            raw_response = self.llm.query(selection_prompt)
        except LLMInteractionError as e:
            raise ContextSelectionError(f"Failed to select files: {e}") from e

        # Expecting one file path per line
        selected_files_raw = [line.strip() for line in raw_response.splitlines() if line.strip()]

        # Validate Gemini output paths
        valid_selected_files = []
        file_structure_set = set(file_structure)

        for file_path in selected_files_raw:
            # Sanitize file path
            sanitized_path = file_path.strip('/')
            if sanitized_path in file_structure_set:
                valid_selected_files.append(sanitized_path)
            else:
                logging.warning(f"Found invalid/unknown file path: '{file_path}'")

        if not valid_selected_files:
            raise ContextSelectionError("No valid file paths found by LLM.")

        if len(valid_selected_files) > self.max_context_files:
            logging.debug(f"Found {len(valid_selected_files)} relevant files, limiting to {self.max_context_files}.")
            final_selection = valid_selected_files[:self.max_context_files] # Future optimization: prioritize based on file importance
        else:
            final_selection = valid_selected_files

        logging.debug(f"Selected {len(final_selection)} relevant files: {final_selection}")
        logging.info(f"Selected {len(final_selection)} relevant files.")
        return final_selection


    def build_context_string(self, selected_files: list, repo_data: dict) -> str:
        """
        Constructs the final context string from the content of selected files.
        """
        context_parts = []
        total_tokens = 0

        separator = "\n\n"

        for file_path in selected_files:
            if file_path not in repo_data:
                logging.warning(f"Could not find '{file_path}' in loaded repository data, skipping.")
                continue

            content = repo_data[file_path]
            if not content.strip():
                 continue

            header = f"----- File: {file_path} -----\n"

            current_context = header + content
            try:
                count_response = self.llm.model.count_tokens(current_context)
                current_file_tokens = count_response.total_tokens

            except Exception as e:
                logging.warning(f"Call count_tokens failed for file_path={file_path}, skipping file. Error={e}")
                continue

            if total_tokens + current_file_tokens <= self.max_total_context_tokens:
                context_parts.append(current_context)
                total_tokens += current_file_tokens
            else:
                logging.warning(f"File with file_path={file_path} exceed max_total_context_tokens={self.max_total_context_tokens}, skipping remaining files.")
                break

        logging.debug(f"Built final context string with total_tokens={total_tokens}.")

        return separator.join(context_parts)