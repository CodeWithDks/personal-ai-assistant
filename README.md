# 🤖 Personal AI Assistant

An AI-powered personal productivity assistant that helps you manage your daily tasks and notes using natural language. Built with **LangChain**, **OpenAI**, **FastAPI**, **Streamlit**, and **SQLite**, this project demonstrates how Large Language Models (LLMs) can interact with real-world tools and databases to automate personal productivity.

> 🚧 **Project Status:** Under Active Development

---

# ✨ Features

* 💬 Chat with an AI assistant using natural language
* ✅ Create, update, delete, and view tasks
* 📝 Create, update, delete, and retrieve notes
* 🧠 Tool-calling AI agent powered by LangChain
* ⚡ FastAPI backend for APIs and business logic
* 🎨 Streamlit frontend for an interactive user interface
* 🗄️ SQLite database for persistent storage
* 🔄 Modular project architecture for easy scalability

---

# 🛠️ Tech Stack

| Technology | Purpose              |
| ---------- | -------------------- |
| Python     | Programming Language |
| LangChain  | AI Agent Framework   |
| OpenAI GPT | Large Language Model |
| FastAPI    | Backend API          |
| Streamlit  | Frontend UI          |
| SQLAlchemy | ORM                  |
| SQLite     | Database             |
| Pydantic   | Data Validation      |
| Uvicorn    | ASGI Server          |

---

# 📁 Project Structure

```text
personal-ai-assistant/
│
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   │   ├── agent.py
│   │   │   ├── llm.py
│   │   │   ├── prompts.py
│   │   │   └── tools/
│   │   │       ├── notes.py
│   │   │       └── tasks.py
│   │   │
│   │   ├── database/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── main.py
│   │
│   └── requirements.txt
│
├── frontend/
│   ├── ui.py
│   └── requirements.txt
│
├── .env
├── .gitignore
├── README.md
└── LICENSE
```

---

# 🚀 Getting Started

## 1. Clone the Repository

```bash
git clone https://github.com/your-username/personal-ai-assistant.git

cd personal-ai-assistant
```

---

## 2. Create a Virtual Environment

```bash
python -m venv .venv
```

Activate it:

### Windows

```bash
.venv\Scripts\activate
```

### Linux / macOS

```bash
source .venv/bin/activate
```

---

## 3. Install Dependencies

Backend:

```bash
cd backend

pip install -r requirements.txt
```

Frontend:

```bash
cd ../frontend

pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file in the project root.

```env
OPENAI_API_KEY=your_openai_api_key
```

---

## 5. Start the FastAPI Backend

From the project root:

```bash
uvicorn backend.app.main:app --reload
```

The backend will be available at:

```
http://localhost:8000
```

API documentation:

```
http://localhost:8000/docs
```

---

## 6. Start the Streamlit Frontend

Open a new terminal:

```bash
streamlit run frontend/ui.py
```

The application will be available at:

```
http://localhost:8501
```

---

# 🧠 AI Capabilities

The assistant can understand natural language requests such as:

* "Create a task to finish my project tomorrow."
* "Show all my pending tasks."
* "Delete my shopping note."
* "Create a note about today's meeting."
* "Update my math task to 5 PM."

The AI automatically selects the appropriate tool to perform the requested action.

---

# 📌 Current Features

### Tasks

* Create tasks
* View tasks
* Update tasks
* Delete tasks

### Notes

* Create notes
* View notes
* Update notes
* Delete notes

---

# 🔮 Planned Features

* User authentication
* Conversation memory
* Semantic search for notes
* Task reminders
* Calendar integration
* Voice assistant
* Email integration
* PDF document understanding
* RAG (Retrieval-Augmented Generation)
* Multi-agent workflows
* Docker support
* Cloud deployment
* Unit and integration tests

---

# 📷 Screenshots

You can add screenshots here once the UI is complete.

```text
assets/
├── home.png
├── chat.png
└── tasks.png
```

---

# 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create a feature branch

```bash
git checkout -b feature/new-feature
```

3. Commit your changes

```bash
git commit -m "Add new feature"
```

4. Push to your branch

```bash
git push origin feature/new-feature
```

5. Open a Pull Request

---

# 📜 License

This project is licensed under the MIT License.

---

# 👨‍💻 Author

**Your Name**

GitHub: https://github.com/your-username

LinkedIn: https://linkedin.com/in/your-profile

---

⭐ If you found this project helpful, consider giving it a star on GitHub!
