# CodeBot - Focus AI Assignment
# Author: Gianmaria Biselli

## Setup

1.  **Go to CodeBot directory**

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
python -m chatbot.main path/to/your/code/repo -q "Your question about the code?"
```

To change the log level, add the `--log-level` flag:

```bash
python -m chatbot.main path/to/your/code/repo -q "Your question about the code?" --log-level {INFO, DEBUG, ERROR}
```