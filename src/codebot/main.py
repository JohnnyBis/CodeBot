import argparse
import logging
import sys

from .utils.utils import load_config
from .repository_loader import RepositoryLoader
from .gemini_interface import GeminiInterface
from .prompt_manager import PromptManager
from .context_selector import ContextSelector
from .exceptions import CodeBotError, RepoProcessingError, ContextSelectionError, LLMInteractionError

def run_CodeBot(repo_path: str, query: str):
    """
    Main function to run CodeBot.

    Args:
        repo_path (str): Path to the code repository.
        query (str): User's question about the repository.
    """

    try:
        config = load_config()
        if not config:
            raise CodeBotError("Failed to load configuration file 'config.yaml'.")

        repo_loader = RepositoryLoader(config)
        gemini_interface = GeminiInterface(config)
        prompt_manager = PromptManager()
        context_selector = ContextSelector(config, gemini_interface, prompt_manager)

    except LLMInteractionError as e:
         logging.error(f"Failed to initialize model: {e}")
         sys.exit(1)
    except CodeBotError as e:
        logging.error(f"CodeBot initialization failed: {e}")
        sys.exit(1)
    except Exception as e:
        logging.exception("Unexpected error during initialization: ", e)
        sys.exit(1)

    final_answer = ""
    try:
        repo_data = repo_loader.load_repository(repo_path)
        logging.debug(f"Repository loading complete. {len(repo_data)} files loaded.")

        file_structure = repo_loader.get_file_structure(repo_data)
        if not file_structure:
             logging.error("No files based on config.")
             return
        
        logging.info("Processing your question...")
        
        # Select Context
        selected_files = context_selector.select_relevant_files(query, file_structure)

        if not selected_files:
            logging.warning("No relevant files found - attempting to answer without specific code context.")

            context_str = "(No specific code context could be reliably selected for this query based on file names. The following answer is based on general knowledge or the query itself.)"
        else:
            context_str = context_selector.build_context_string(selected_files, repo_data)

        # Generate answer using selected context
        answer_prompt = prompt_manager.format_answer_prompt(query, context_str)
        final_answer = gemini_interface.query(answer_prompt)

        print("\n--- CodeBot says ---")
        print(final_answer)

    except RepoProcessingError as e:
        logging.error(f"Failed to load repository: {e}", exc_info=True)
        sys.exit(1)
    except ContextSelectionError as e:
        logging.error(f"Failed to select context: {e}", exc_info=True)
        sys.exit(1)
    except LLMInteractionError as e:
        logging.error(f"LLM interaction failed during workflow: {e}", exc_info=True)
        sys.exit(1)
    except CodeBotError as e:
        logging.error(f"CodeBot error occurred: {e}", exc_info=True)
        sys.exit(1)
    except Exception as e:
        logging.exception("An unexpected error occurred during CodeBot execution", e)
        sys.exit(1)

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
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level."
    )

    args = parser.parse_args()

    logging.getLogger().setLevel(args.log_level)

    run_CodeBot(args.repo_path, args.query)

if __name__ == "__main__":
    main_codebot_cli()