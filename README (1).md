# 🚀 Amazon Data AI Assistant - Tips Hindawi Challenge (June–July) 2026

> 🏆 This repository is my official submission for the [ **Tips Hindawi** ](https://www.tipshindawi.com/) **Challenge (June–July) 2026**.

## 👤 Participant

| Field            | Value                                |
| ---------------- | ------------------------------------ |
| Full Name        | Ahmad Essam Elsherif                 |
| Project Name     | Amazon SQL & Business AI Agent       |
| GitHub Username  | ahmadessam                           |
| Challenge Batch  | June–July 2026                       |
| Training Program | Large Language Models (LLMs) Program |
| Organization     | [**Edrak for Ai**](https://edrak4ai.com/en) |

---

# 📖 Project Overview

**Amazon Data AI Assistant** is an intelligent conversational agent built to query, analyze, and generate strategic business insights from e-commerce relational databases (SQLite). 

By combining **LangChain**, **Ollama (Llama 3)**, and **RAG (Retrieval-Augmented Generation)**, the assistant automatically routes queries, dynamically generates and corrects SQLite queries, retrieves domain rules from a Knowledge Base, and presents analytical summaries with actionable business recommendations in Arabic.

---

# ✨ Features

* **Smart Intent Routing:** Automatically differentiates between casual conversation (`GENERAL`) and database querying (`DATA_QUERY`).
* **Text-to-SQL Generation:** Translates natural language questions into clean SQLite queries.
* **Self-Healing SQL Executions:** Detects database query errors and automatically corrects the SQL logic in real-time.
* **RAG Integration:** Uses FAISS vector store to retrieve domain knowledge (`.md` rules) to enforce strict business metrics and query aliases.
* **Arabic Business Analysis:** Analyzes real-time database results and provides clear recommendations without language mixing or mathematical hallucinations.
* **Interactive Streamlit Interface:** Modern RTL-supported Streamlit UI complete with query history, dataframe rendering, and SQL inspection expanders.

---

# 🛠️ Technologies Used

* **Language Model:** Ollama (`llama3`)
* **Framework:** LangChain & LangChain Community
* **Vector Store & Embeddings:** FAISS & HuggingFace (`all-MiniLM-L6-v2`)
* **Database:** SQLite & Pandas
* **UI Framework:** Streamlit (with custom CSS for RTL support)
* **Language:** Python 3.10+

---

# ⚙️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ahmadessam/amazon-sql-ai-agent.git
   cd amazon-sql-ai-agent
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install streamlit langchain langchain-ollama langchain-community langchain-huggingface faiss-cpu pandas
   ```

4. **Prepare the database:**
   Run the database creation script to generate `store.db` from your Amazon CSV file:
   ```bash
   python build_db.py
   ```

5. **Make sure Ollama is running Llama 3 locally:**
   ```bash
   ollama run llama3
   ```

---

# 🚀 Usage

Run the Streamlit app:
```bash
streamlit run app.py
```

Open your browser at `http://localhost:8501` and start asking questions like:
* *"كم عدد الطلبات المعلقة ومجموع قيمتها المالية؟"*
* *"هات أعلى 5 منتجات مبيعا في المتجر"*
* *"إيه أكتر فئة مبيعاً من حيث الكمية؟"*

---

# 📚 Knowledge Base Structure

The project utilizes a `knowledge/` folder containing Markdown files for RAG context retrieval:
* `business_rules.md`: Defines order statuses and terminology mappings.
* `schema_guidelines.md`: Outlines column ownership and strict aggregation rules.
* `few_shot_examples.md`: Provides sample SQL query patterns.

---

# 📚 About the Challenge

This project was developed as part of the [**Tips Hindawi**](https://www.tipshindawi.com/) **Challenge (June–July) 2026**.

[Tips Hindawi](https://www.tipshindawi.com/) is the internships department of [**Edrak for Ai**](https://edrak4ai.com/en), encouraging participants to build real-world LLM projects and apply practical engineering skills.

---

# 📄 License

This project is shared for educational and portfolio purposes.
