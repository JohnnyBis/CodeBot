# CodeBot - Focus AI Assignment
### Author: Gianmaria Biselli

This CodeBot can do the following:
1. Summarize what the repository is about
2. Tell you what a specific function/class does, including adding code snippets and line numbers were necessary.
3. Answers general questions about your repository.
4. Extension feature (Git commit history):
   1. Tells you the git history of a specific file. 
   2. Tell you who commited a specific file. 
   3. Answers general git history related questions.

A few things to keep in mind:
- If searching for a specific method, it might be useful to give CodeBot some context so it can find the file associated with that method.

## Setup

1.  **Go to the CodeBot directory**

2.  **Start Virtual Environment:**
    ```bash
    python -m venv venv

    source venv/bin/activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Update Gemini API Key in .env file:**
    ```env
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
    ```

## Usage

Open your terminal and provide the path to the repository you want to query and your question using the `-q` flag.

```bash
python -m src.codebot.main path/to/your/code/repo -q "What does function X do in Y class/file?"
python -m src.codebot.main path/to/your/code/repo -q "When was the last commit of the X java file?"
python -m src.codebot.main path/to/your/code/repo -q "Give me the git history of the X java file?"
```

To change the log level, add the `--log-level` flag:

```bash
python -m src.codebot.main path/to/your/code/repo -q "Your question about the code?" --log-level {INFO, DEBUG, ERROR}
```