class CodeBotError(Exception):
    """Base exception for the application."""

    def __init__(self, message="An error occurred in the application."):
        self.message = message
        super().__init__(self.message)


class RepoProcessingError(CodeBotError):
    """Exception raised during repository processing."""

    def __init__(self, message="Error processing repository code."):
        super().__init__(message)


class ContextSelectionError(CodeBotError):
    """Exception raised during context selection or building."""

    def __init__(self, message="Error selecting or building context for the LLM."):
        super().__init__(message)


class LLMInteractionError(CodeBotError):
    """Exception raised during interaction with the LLM API."""

    def __init__(self, message="Error interacting with the LLM API."):
        super().__init__(message)


class GitExecutionError(CodeBotError):
    """Exception raised during Git command execution."""

    def __init__(self, message="Error during Git command execution."):
        super().__init__(message)
