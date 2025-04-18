class PromptManager:
    """Formats prompts for different tasks."""

    # Prompt for selecting relevant files
    CONTEXT_SELECTION_PROMPT = """
    You are a helpful AI code assistant. Your task is to help determine which code files are relevant to a user's query about a software repository.
    Your goal is to output a list of file paths that likely contain the information needed to answer the query.

    User Query: "{query}"

    Available files in the repository (relative paths):
    {file_list}

    Instructions:
    1. Analyze the "User Query" and the list of "Available Files".
    2. Identify the file paths that are *most likely* relevant to answering the query.
    3. Consider file names, directory structure, and common conventions (e.g., 'utils', 'models', 'controllers', 'tests').
    4. If the query is broad (e.g., "summarize the project", "what does it do?", "find dependencies"), list a broader set of key files or potentially all files if the repository is small.
    5. If the query refers to a specific file or function, prioritize that file and potentially related ones (e.g., where it's used or defined).
    6. Output *only* the list of relevant file paths, each on a new line. Do not include any explanations, preamble, or formatting like bullet points or backticks.

    Restrictions:
    - Ignore files that are:
        - Found within directories like ".git/", ".gradle/", ".idea/", "node_modules/", "build/", "dist/".
        - End with extensions usually irrelevant for source code analysis, such as ".jar", ".bin", ".exe", ".dll", ".log".
        - Common configuration files that aren't usually queried directly, unless the query *is* about them.
    
    Relevant files:
    """

    # Prompt for answering the user's query using selected context
    ANSWER_PROMPT = """
    You are a helpful AI code assistant. Your task is to answer the user's query based *strictly* on the provided code context.

    Instructions:
    1. Read the "User Query".
    2. Analyze the provided "Code Context", which contains snippets or full contents of relevant files.
    3. Formulate an answer to the "User Query" using *only* information found in the "Code Context".
    4. Do *NOT* make up information, make assumptions, or use any knowledge outside the provided "Code Context".
    5. If the context does not contain the information needed to answer the query, state that clearly (e.g., "Based on the provided context, I cannot answer that question.").
    6. Structure your answer clearly and concisely. Use markdown formatting where appropriate (e.g., code snippets, lists).

    Important Notes:
    When referencing code, state the file path and either:
        a) Mention the specific function/class name (e.g., "in the `calculate_sum` function...").
        b) Provide the relevant line numbers (e.g., "... as seen on lines 42-45.").
        c) Quote short, relevant code snippets using backticks (e.g., "it uses `requests.get(url)` to fetch data.").

    **User Query:** "{query}"

    **Code Context:**
    --- BEGIN CONTEXT ---
    {context}
    --- END CONTEXT ---

    **Answer:**
    """

    # Prompt to get the right Git command based on the user's git-related question.
    GIT_COMMAND_PROMPT = """
    You are a helpful AI code assistant. Your task is to help a user query Git history for a code repository.
    Based on the user's query and the target file, determine the most appropriate and **safe** `git` command(s) to retrieve the necessary information (e.g., author, date, commit message, commit hash).

    Constraints:
    - Only generate **read-only** commands (primarily `git log` and `git blame`). Do NOT generate commands that modify history or the working directory.
    - Use common flags that provide easily parsable output (e.g., `--pretty=format:...`, `--porcelain` for blame, `--date=iso`).
    - Assume commands will be run from the repository root. Use relative paths for files as provided.
    - If multiple commands are needed, list each on a new line.
    
    Output: 
    - For the output, **ONLY** return the raw command(s) and nothing else.

    **User Query:** "{query}"
    **Target File:** "{filepath}"
    """

    GIT_ANSWER_SYNTHESIS_PROMPT = """
    You are a helpful AI code assistant. Your task is to answer a user's question about Git history.
    The user originally asked: "{query}"

    To answer this, the following Git command(s) were executed:
    {git_commands}
    
    The output from the command(s) was:
    {git_output}
    
    Based only on the Git command output provided above, formulate a concise and natural language answer to the user's original query.
        - Do not make up information not present in the Git output.
        - If the output contains the requested information (like author, date, commit details), present it clearly.
        - If the output indicates an error (e.g., file not found, command failed) or contains no relevant information, state that clearly in your answer.
        For e.g., you could say "Sorry I wasn't able to find anything relevant to your question." or "The Git command failed with an error: [error message]".
    
    **Answer:**
    """

    # New prompt to parse the Git query target using LLM
    GIT_TARGET_PARSING_PROMPT = """
    You are a helpful AI code assistant. Your task is to parse a user's query about Git history to identify the specific target file.

    **Instructions:**
    1. Analyze the "User Query" provided below.
    2. Identify the relative file path the user is asking about based on the provided "Context".
    3. If the query is vague like "X file", take into account the file extensions when you're searching.
    4. If the query is vague, give your best guess (i.e. the most likely file they're describing).
    5. Output the results ONLY in the following format, ensuring each label is on a new line:
       FILENAME: path/to/your/file.ext
    7. If no specific file path can be reliably identified, output `FILENAME: None`.
    
    Important:
    - Do not include any other text, explanation, or formatting.

    **Context:**
    {file_list_context}

    **User Query:** "{query}"

    **Parsed Output:**
    FILENAME: <YOUR ANSWER>
    """

    def format_selection_prompt(self, query: str, file_list: list) -> str:
        """Formats the prompt to select the context based on a list of files."""
        if not file_list:
            file_list_str = "**No files available**"
        else:
            file_list_str = "\n".join(sorted(file_list))

        return self.CONTEXT_SELECTION_PROMPT.format(query=query, file_list=file_list_str)

    def format_answer_prompt(self, query: str, context_str: str) -> str:
        """Formats the prompt to answer the user's question."""
        context_str = context_str if context_str else "**No specific code context was provided for this query.**"

        return self.ANSWER_PROMPT.format(query=query, context=context_str)

    def format_git_target_parse_prompt(self, query: str, file_list: list = None) -> str:
        """Formats the prompt to ask the LLM to find the target of the Git-related question."""

        if file_list:
            # If too many files...
            limit = 200
            if len(file_list) > limit:
                context_str = "\n".join(file_list[:limit]) # Improvement: Prioritize the most relevant files
            else:
                context_str = "\n".join(file_list)
        else:
            context_str = "**File list not provided**"

        return self.GIT_TARGET_PARSING_PROMPT.format(
            query=query,
            file_list_context=context_str
        )

    def format_git_command_prompt(self, query: str, filepath: str) -> str:
        """Formats the prompt to ask the LLM for Git commands."""

        return self.GIT_COMMAND_PROMPT.format(
            query=query,
            filepath=filepath,
        )

    def format_git_synthesis_prompt(self, query: str, git_commands: str, git_output: str) -> str:
        """Formats the prompt to give the final answer based on the Git output."""

        commands = str(git_commands).strip() if git_commands else "**No command executed**"
        output = str(git_output).strip() if git_output else "**No output**"

        return self.GIT_ANSWER_SYNTHESIS_PROMPT.format(
            query=query,
            git_commands=commands,
            git_output=output
        )