import logging
from pathlib import Path
from .utils.utils import count_tokens, truncate_text
from .exceptions import RepoProcessingError

class RepositoryLoader:
    """Handles loading and preprocessing of files from a code repository."""

    def __init__(self, config):
        """
        Initializes the loader with configuration settings.

        Args:
            config (dict): Configuration dictionary, expects 'repository' key.
        """
        if not config or 'repository' not in config:
            logging.warning("Repository configuration missing, using default settings.")
            self.config = {}
        else:
            self.config = config.get('repository', {})

        # Set defaults if keys are missing in the loaded config
        self.ignore_dirs = set(self.config.get('ignore_dirs', ['.git', '__pycache__']))
        self.ignore_files = set(self.config.get('ignore_files', ['.env']))
        self.max_file_tokens = self.config.get('max_file_tokens', 2000)

    def load_repository(self, repo_path_str: str) -> dict:
        """
        Loads files from the specified repository path.

        Args:
            repo_path_str (str): The path to the root of the repository.

        Returns:
            dict: A dictionary where keys are relative file paths (str)
                  and values are the content of the files (str).

        Raises:
            RepoProcessingError: If the repository path is invalid or no files could be loaded.
        """
        repo_path = Path(repo_path_str).resolve() # Resolve to absolute path
        if not repo_path.is_dir():
            raise RepoProcessingError(f"Repository path not found or is not a directory: {repo_path}")

        logging.info(f"Scanning repository: {repo_path}")
        code_files = {}
        file_load_errors = []

        for item_path in repo_path.rglob('*'):
            if self._is_ignored(item_path, repo_path):
                continue

            if item_path.is_file():
                try:
                    relative_path = str(item_path.relative_to(repo_path))

                    with open(item_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    token_count = count_tokens(content)
                    if token_count > self.max_file_tokens:
                        logging.debug(f"File {relative_path} ({token_count} tokens) exceeds max tokens ({self.max_file_tokens}). Truncating.")
                        content = truncate_text(content, self.max_file_tokens)
                    elif token_count == 0 and len(content) > 0:
                         logging.debug(f"File {relative_path} has content but counted 0 tokens. Check tokenization.")
                    elif token_count == 0 and len(content) == 0:
                         logging.debug(f"File {relative_path} is empty.")

                    code_files[relative_path] = content

                except Exception as e:
                    err_msg = f"Could not read or process file {item_path}: {e}"
                    file_load_errors.append(err_msg)

        if file_load_errors:
            raise RepoProcessingError(f"Encountered errors while loading repository: {file_load_errors}")

        if not code_files:
            raise RepoProcessingError(f"No supported files found in the repository: {repo_path}")

        return code_files

    def get_file_structure(self, code_files: dict) -> list:
        """
        Generates a simple list of file paths from the loaded code files.

        Args:
            code_files (dict): The dictionary returned by load_repository.

        Returns:
            list: A sorted list of relative file paths (str).
        """
        if not code_files:
            return []
        return sorted(list(code_files.keys()))
    
    def _is_ignored(self, path: Path, repo_root: Path) -> bool:
        """Checks if a given path should be ignored based on configuration."""

        if path.name in self.ignore_files:
            return True

        # Check if any part of the path relative to root is an ignored directory
        try:
            relative_parts = path.relative_to(repo_root).parts
            # Check parent directories as well (e.g., ignore 'node_modules/some/file.js')
            if any(part in self.ignore_dirs for part in relative_parts):
                 return True
        except ValueError:
             # This can happen if the path is not relative to the root for some reason
             logging.warning(f"Could not determine relative path for {path} against root {repo_root}")
             # Decide how to handle - safer to ignore if path is weird?
             return True # Let's ignore if relative path fails

        # Check ignored directories by name (for the path itself if it's a directory)
        if path.is_dir() and path.name in self.ignore_dirs:
             return True

        return False