import logging
import subprocess
import shlex
from pathlib import Path
from .gemini_interface import GeminiInterface
from .prompt_manager import PromptManager
from .exceptions import GitExecutionError
from typing import Union


class GitAssistant:
    """Handles queries related to Git history."""

    ALLOWED_GIT_COMMANDS = {'log', 'blame'}
    GIT_KEYWORDS: set[str] = {
        "who updated",
        "who modified",
        "who last modified",
        "who changed",
        "when was",
        "last commit",
        "last commited",
        "git history",
        "author",
        "authors",
        "last change",
        "blame"
    }

    def __init__(self, llm_interface: GeminiInterface, prompt_manager: PromptManager):
        self.llm = llm_interface
        self.prompter = prompt_manager

    def is_query_git_related(self, query: str) -> bool:
        """Checks if the query seems related to Git history."""

        query_lower = query.lower()
        for keyword in self.GIT_KEYWORDS:
            if keyword in query_lower:
                return True

        return False

    def _validate_git_command(self, command_str: str) -> Union[list, None]:
        """
        Validates if the LLM-generated git command is safe
        """
        if not command_str:
            return None

        try:
            parts = shlex.split(command_str)
        except ValueError:
            return None

        if len(parts) < 2 or parts[0] != 'git':
            logging.error(f"Not a git command: {command_str}")
            return None

        if parts[1] not in self.ALLOWED_GIT_COMMANDS:
            logging.error(f"Command not allowed: {command_str}")
            return None

        return parts

    def parse_target(self, query: str, file_structure: list = None) -> Union[str, None]:
        """
        Parse the filename from the query.
        """

        try:
            prompt = self.prompter.format_git_target_parse_prompt(query, file_structure)
            response = self.llm.query(prompt)

            filename = None

            for line in response.strip().splitlines():
                if line.startswith("FILENAME:"):
                    filename = line.split(":", 1)[1].strip()

                    if filename.lower() == 'none':
                        filename = None

            logging.debug(f"Parsed successfully, file={filename}")
            return filename
        except Exception as e:
            logging.error(f"Failed to parse response, exception={e},")
            raise e

    def handle_query(self, repo_root_path_str: str, query: str, target_file_path: str) -> str:
        """
        Handles the Git related query.
        """

        repo_root = Path(repo_root_path_str).resolve()

        if not repo_root.is_dir() or not (repo_root / ".git").is_dir():
            raise GitExecutionError(f"Error: Invalid Git repository path: {repo_root}")

        command_gen_prompt = self.prompter.format_git_command_prompt(
            query, target_file_path
        )

        try:
            suggested_commands_str = self.llm.query(command_gen_prompt)
            logging.info(f"Suggested relevant Git command(s):\n{suggested_commands_str.strip()}")
        except Exception as e:
            raise e

        executed_commands = []
        final_output_log = []
        valid_command_found = False

        for command_str in suggested_commands_str.strip().splitlines():

            validated_command_parts = self._validate_git_command(command_str.strip())

            if not validated_command_parts:
                continue

            executed_commands.append(command_str)

            try:
                result = subprocess.run(
                    validated_command_parts, cwd=repo_root, capture_output=True, text=True,
                    check=True, encoding='utf-8', errors='ignore'
                )

                valid_command_found = True
                final_output_log.append(result.stdout.strip())
            except Exception as e:
                # Don't stop - try the next command
                logging.debug(e)

        if not valid_command_found:
            raise GitExecutionError("Could not find any valid Git commands to execute for the user's query.")

        synthesis_prompt = self.prompter.format_git_synthesis_prompt(
            query,
            "\n".join(executed_commands),
            "\n---\n".join(final_output_log).strip()
        )

        try:
            final_answer = self.llm.query(synthesis_prompt)
            return final_answer
        except Exception as e:
            raise e
