import logging
from pathlib import Path
from .exceptions import RepoProcessingError

class RepositoryLoader:
    """Handles loading and preprocessing of files from a code repository."""

    def __init__(self, config):
        """
        Initializes the loader with configuration settings.
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
        """
        repo_path = Path(repo_path_str).resolve()

        if not repo_path.is_dir():
            raise RepoProcessingError(f"Repository path not found or is not a directory: {repo_path}")

        logging.info(f"Scanning repository: {repo_path}")
        code_files = {}

        for item_path in repo_path.rglob('*'):
            if self._is_ignored(item_path, repo_path):
                continue

            if item_path.is_file():
                try:
                    relative_path = str(item_path.relative_to(repo_path))

                    with open(item_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

                    if len(content) == 0:
                        logging.debug(f"File {relative_path} is empty.")

                    # Improvements: Check token size of the content and truncate based on query relevance.
                    code_files[relative_path] = content

                except Exception as e:
                    raise RepoProcessingError(f"Failed to load file {item_path}: {e}")

        if not code_files:
            raise RepoProcessingError(f"No supported files found in the repository: {repo_path}")

        return code_files

    def _is_ignored(self, path: Path, repo_root: Path) -> bool:
        """Checks if a given path should be ignored based on the configs."""

        if path.name in self.ignore_files:
            return True

        # Check if any part of the path relative to root is an ignored directory
        try:
            relative_parts = path.relative_to(repo_root).parts

            if any(part in self.ignore_dirs for part in relative_parts):
                 return True

        except ValueError:
             return True

        return False