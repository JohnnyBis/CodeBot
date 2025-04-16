import logging
from .gemini_interface import GeminiInterface
from .prompt_manager import PromptManager
from .utils.utils import count_tokens, truncate_text
from .exceptions import ContextSelectionError, LLMInteractionError

class ContextSelector:
    """
    Selects relevant code context for a given query using an LLM-based approach.
    """

    def __init__(self, config: dict, gemini_interface: GeminiInterface, prompt_manager: PromptManager):
        """
        Initializes the ContextSelector.

        Args:
            config (dict): Application configuration, expecting 'repository' and 'llm' keys.
            gemini_interface (GeminiInterface): Instance for interacting with Gemini.
            prompt_manager (PromptManager): Instance for formatting prompts.
        """
        self.repo_config = config.get('repository', {})
        self.llm_config = config.get('llm', {})
        self.llm = gemini_interface
        self.prompter = prompt_manager

        # Configuration for context limits
        self.max_context_files = self.repo_config.get('max_context_files', 5)
        self.max_total_context_tokens = self.llm_config.get('max_context_tokens', 8000)

    def select_relevant_files(self, query: str, file_structure: list) -> list:
        """
        Uses Gemini to identify relevant files based on names and the query.

        Args:
            query (str): The user's query.
            file_structure (list): A list of relative file paths in the repository.

        Returns:
            list: A list of selected relevant file paths (subset of file_structure).

        Raises:
            ContextSelectionError: If the LLM fails to provide a usable selection.
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

        Args:
            selected_files (list): Selected relevant file paths (relative path).
            repo_data (dict): Maps file path to its content.

        Returns:
            str: A single string containing the formatted content of the selected files.
        """
        context_parts = []
        total_tokens = 0
        separator = "\n\n" + "="*20 + "\n\n" # Separator between files

        # Estimate separator tokens (rough)
        separator_tokens = count_tokens(separator)

        for file_path in selected_files:
            if file_path not in repo_data:
                logging.warning(f"Selected file path '{file_path}' not found in loaded repository data - skipping.")
                continue

            content = repo_data[file_path]
            header = f"--- File: {file_path} ---\n"
            header_tokens = count_tokens(header)
            content_tokens = count_tokens(content)

            # Calculate tokens needed for this file (header + content + separator)
            # Add separator tokens only if this is not the first file
            needed_tokens = header_tokens + content_tokens + (separator_tokens if context_parts else 0)

            if total_tokens + needed_tokens <= self.max_total_context_tokens:
                # Add the file content
                context_parts.append(header + content)
                total_tokens += needed_tokens
                logging.debug(f"Added file '{file_path}' to context ({content_tokens} tokens). Total tokens: {total_tokens}")
            else:
                # File doesn't fit fully, try truncating
                available_tokens = self.max_total_context_tokens - total_tokens - header_tokens - (separator_tokens if context_parts else 0)
                logging.debug(f"File '{file_path}' ({content_tokens} tokens) exceeds context limit ({self.max_total_context_tokens} total). Trying to truncate.")

                # Only add truncated version if there's meaningful space available
                min_meaningful_tokens = 50 # Don't add tiny truncated snippets
                if available_tokens > min_meaningful_tokens:
                    truncated_content = truncate_text(content, available_tokens)
                    truncated_tokens = count_tokens(truncated_content) # Recalculate after truncation

                    context_parts.append(header + truncated_content)
                    total_tokens += header_tokens + truncated_tokens + (separator_tokens if context_parts else 0)
                    logging.debug(f"Added truncated file '{file_path}' to context ({truncated_tokens} tokens). Total tokens: {total_tokens}")
                else:
                    logging.debug(f"Not enough space ({available_tokens} tokens) to add even a truncated version of '{file_path}'. Skipping.")

                # Stop adding more files once limit is hit or exceeded
                break

        return separator.join(context_parts)