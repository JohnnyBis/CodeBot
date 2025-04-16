class PromptManager:
    """Manages and formats prompts for different tasks."""

    # Prompt for selecting relevant files
    CONTEXT_SELECTION_PROMPT = """
        You are a helpful AI code assistant. Your task is to help determine which code files are relevant to a user's query about a software repository.
        Your goal is to output a list of file paths that likely contain the information needed to answer the query.

        User Query: "{query}"

        Available files in the repository (relative paths):
        {file_list}

        Instructions:
        1. Analyze the User Query and the list of Available Files.
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

        **Crucial Note** 
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

    def format_selection_prompt(self, query: str, file_list: list) -> str:
        """Formats the prompt to select the context based on a list of files."""
        if not file_list:
            file_list_str = "(No files available)"
        else:
            file_list_str = "\n".join(sorted(file_list))

        return self.CONTEXT_SELECTION_PROMPT.format(query=query, file_list=file_list_str)

    def format_answer_prompt(self, query: str, context_str: str) -> str:
        """Formats the final prompt to answer the user's question."""

        if not context_str:
            context_str = "(No specific code context was provided for this query.)"

        return self.ANSWER_PROMPT.format(query=query, context=context_str)
    