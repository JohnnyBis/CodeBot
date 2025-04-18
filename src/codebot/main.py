import argparse
import logging
import sys

from src.codebot.git_assistant import GitAssistant
from .utils.utils import load_config, get_file_structure
from .repository_loader import RepositoryLoader
from .gemini_interface import GeminiInterface
from .prompt_manager import PromptManager
from .context_selector import ContextSelector
from .exceptions import CodeBotError, RepoProcessingError


def run_code_bot(repo_path: str, query: str):
    """
    Main function to run CodeBot.
    """

    try:
        config = load_config()
        if not config:
            raise CodeBotError("Failed to load configuration file 'config.yaml'.")

        repo_loader = RepositoryLoader(config)
        gemini_interface = GeminiInterface(config)
        prompt_manager = PromptManager()
        git_assistant = GitAssistant(gemini_interface, prompt_manager)
        context_selector = ContextSelector(config, gemini_interface, prompt_manager)

    except Exception as e:
        logging.exception("Unexpected error during initialization: ", e)
        sys.exit(1)

    try:
        repo_data = repo_loader.load_repository(repo_path)
        logging.debug(f"Repository loading complete. {len(repo_data)} files loaded.")

        file_structure = get_file_structure(repo_data)
        if not file_structure:
             logging.error("No files based on config.")
             return

        logging.info("Processing your question...")

        final_answer = None

        if git_assistant.is_query_git_related(query):
            logging.info("Git related query detected.")

            try:
                target_file = git_assistant.parse_target(query, file_structure)

                if not target_file:
                    final_answer = "Sorry, I couldn't identify a specific file based on your query."
                else:
                    final_answer = git_assistant.handle_query(
                        repo_path,
                        query,
                        target_file
                    )
            except Exception as e:
                logging.exception(f"Unexpected exception: {e}")
                sys.exit(1)
        else:
            selected_files = context_selector.select_relevant_files(query, file_structure)

            if not selected_files:
                logging.warning("No relevant files found - attempting to answer without specific code context.")
                context_str = "**No specific code context could be selected for this query based on file names. Answer as best as possible.**"
            else:
                context_str = context_selector.build_context_string(selected_files, repo_data)

            # Generate answer using selected context
            answer_prompt = prompt_manager.format_answer_prompt(query, context_str)
            final_answer = gemini_interface.query(answer_prompt)

        print("\n--- CodeBot says ---")
        print(final_answer + "\n")
    except RepoProcessingError as e:
        print("\n--- CodeBot says ---")
        print("Oops, repository could not be found. Please check your repository path and try again.\n")
        logging.error(f"Repository processing error: {e}")
    except Exception as e:
        print("\n--- CodeBot says ---")
        print("Oops, something unexpected happend...\n")
        logging.error(f"An unexpected error occurred during CodeBot execution: {e}")

def main_codebot_cli():
    """Parses command line arguments and runs the CodeBot."""
    
    parser = argparse.ArgumentParser(
        description="CodeBot analyzes your code repository.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        "repo_path",
        help="Path to the code repository directory."
    )

    parser.add_argument(
        "-q", "--query",
        required=True,
        help="Question about the repository."
    )

    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Set the logging level."
    )

    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)

    run_code_bot(args.repo_path, args.query)

if __name__ == "__main__":
    main_codebot_cli()