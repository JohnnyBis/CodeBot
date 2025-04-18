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
python -m src.codebot.main path/to/your/code/repo -q "Summarize this repo. Be detailed."
python -m src.codebot.main path/to/your/code/repo -q "What does function X do in Y class/file?"
python -m src.codebot.main path/to/your/code/repo -q "When was the last commit of the X java file?"
python -m src.codebot.main path/to/your/code/repo -q "Give me the git history of the X java file?"
```

To change the log level, add the `--log-level` flag:

```bash
python -m src.codebot.main path/to/your/code/repo -q "Your question about the code?" --log-level {INFO, DEBUG, ERROR}
```

Sample Outputs:
```bash
(venv) (base) gianmariabiselli@MacBookPro CodeBot % python -m src.codebot.main /Users/gianmariabiselli/Desktop/order-billing-service -q "Does this repo have Cassandra?"
INFO:root:Scanning repository: /Users/gianmariabiselli/Desktop/order-billing-service
INFO:root:Processing your question...
INFO:root:Selected 7 relevant files.

--- CodeBot says ---
Yes, the repository contains Cassandra. The file `data/cql/orderbillingservice/0.0/002_create_transaction_by_transaction_id_table.cql` creates a table, implying the use of a database, and the `data/cql/orderbillingservice/keyspace.cql` file creates a keyspace, which is a concept used in Cassandra. These files suggest the presence of Cassandra in this repository.
```

```bash
(venv) (base) gianmariabiselli@MacBookPro CodeBot % python -m src.codebot.main /Users/gianmariabiselli/Desktop/order-billing-service -q "What functions does StripePaymentMapper have? list them and explain it"
INFO:root:Scanning repository: /Users/gianmariabiselli/Desktop/order-billing-service
INFO:root:Processing your question...
INFO:root:Selected 1 relevant files.

--- CodeBot says ---
The `StripePaymentMapper` class in `orderbillingservice/src/main/java/com/tabloapp/orderbillingservice/service/mapper/StripePaymentMapper.java` has one function:

*   `fromPaymentIntentRequest`: This function takes a `CreatePaymentIntent` object and a `serviceFeePercentage` as input. It calculates the service fee amount based on the subtotal in the `CreatePaymentIntent` object.  It then returns a `PaymentIntentCreateParams` object, setting the amount, currency, payment method, application fee amount, and transfer data based on the input. The `setDestination` in transfer data is set using `createPaymentIntent.getStripeAccountId()` as seen on line 21.
```

```bash
(venv) (base) gianmariabiselli@MacBookPro CodeBot % python -m src.codebot.main /Users/gianmariabiselli/Desktop/order-billing-service -q "Who last commited the stripe mapper class?"
INFO:root:Scanning repository: /Users/gianmariabiselli/Desktop/order-billing-service
INFO:root:Processing your question...
INFO:root:Git related query detected.
INFO:root:Suggested relevant Git command(s):
git log -n 1 --pretty=format:"%an" orderbillingservice/src/main/java/com/tabloapp/orderbillingservice/service/mapper/StripePaymentMapper.java

--- CodeBot says ---
Gianmaria Biselli last committed the Stripe mapper class.
```
