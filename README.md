<div align="center">

# 🧠 BizRadar AI

### AI-Powered Startup Intelligence & Business Analysis Agent

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-black?style=for-the-badge&logo=ollama&logoColor=white)](https://ollama.com)
[![Llama](https://img.shields.io/badge/Llama-3.2%203B-blueviolet?style=for-the-badge)](https://ollama.com/library/llama3.2)
[![Tavily](https://img.shields.io/badge/Tavily-Search%20API-orange?style=for-the-badge)](https://tavily.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge)]()

**Transform any startup idea into a structured business intelligence report — powered by local AI, real-time web search, and a modular agent architecture.**

[Getting Started](#-getting-started) • [Features](#-features) • [Architecture](#-architecture) • [Roadmap](#-roadmap)

---

</div>

## 🎯 What Is BizRadar AI?

BizRadar AI is a **locally-run AI agent** that takes a raw startup idea and returns a full structured analysis — covering market potential, competitors, MVP features, tech stack recommendations, and risk assessment.

> **Example Input:** `"AI-powered tiffin service for students"`
>
> **Output:** A complete startup analysis report with market insights, MVP suggestions, tech stack, and risk evaluation.

No cloud dependency. No expensive API calls for inference. Runs entirely on your machine via **Ollama + Llama 3.2**.

---

## ✨ Features

| Feature | Description | Status |
|---|---|---|
| 🤖 Local AI Inference | Powered by Ollama + Llama 3.2 3B | ✅ Live |
| 🧠 Context Memory | Remembers last 6 conversation turns | ✅ Live |
| 🔍 Real-Time Web Search | Market analysis via Tavily API | ✅ Live |
| 📊 Startup Analysis | Structured business intelligence report | ✅ Live |
| 💡 MVP Recommendations | Core feature suggestions for launch | ✅ Live |
| 🏗️ Tech Stack Advisor | Frontend, backend, DB, AI recommendations | ✅ Live |
| ⚠️ Risk Analysis | Identifies key business and scaling risks | ✅ Live |
| 🛠️ Modular Tool System | Easily extendable tool architecture | ✅ Live |
| 📚 RAG Pipeline | Document & vector search integration | 🔄 Planned |
| 🤝 Multi-Agent System | Specialized agents working in parallel | 🔄 Planned |

---

## 📁 Project Structure

```
bizradar-ai/
│
├── 🤖 agent.py            # Core AI agent — orchestrates tools + LLM
├── 🖥️  app.py              # CLI entry point
├── 🧠 context_manager.py  # Conversation memory (last 6 turns)
├── 🛠️  tools.py            # Tool layer (search, analysis, MVP, risk)
├── 📝 prompts.py          # System prompt + output format templates
│
├── 🧪 test_api.py         # Ollama API connection test
├── 🧪 test_ollama.py      # Ollama model response test
│
├── 📦 requirements.txt    # Python dependencies
├── 🔒 .env                # API keys (never commit this)
├── 🚫 .gitignore          # Ignores .env and cache files
└── 📖 README.md
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│                   USER INPUT                │
│         "AI tiffin service for students"    │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│              CLI INTERFACE (app.py)         │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│           STARTUP AGENT (agent.py)          │
│                                             │
│  ┌─────────────┐    ┌────────────────────┐  │
│  │   Context   │    │    Tool Layer      │  │
│  │   Manager   │    │                    │  │
│  │             │    │ • search_kb()      │  │
│  │ Last 6 msgs │    │ • analyze_market() │  │
│  └─────────────┘    │ • suggest_mvp()    │  │
│                     │ • recommend_tech() │  │
│                     │ • risk_analysis()  │  │
│                     └────────────────────┘  │
│                                             │
│         ┌───────────────────────┐           │
│         │    PROMPT BUILDER     │           │
│         │  System + Context +   │           │
│         │  Tools + User Input   │           │
│         └───────────────────────┘           │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│         OLLAMA — Llama 3.2 (3B)             │
│           Local Inference Engine            │
└──────────────────────┬──────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────┐
│         STRUCTURED STARTUP REPORT           │
│                                             │
│  # Idea Summary    # Market Potential       │
│  # Competitors     # Suggested MVP          │
│  # Tech Stack      # Risks                  │
│  # Final Verdict                            │
└─────────────────────────────────────────────┘
```

---

## ⚙️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.10+ | Core runtime |
| LLM | Llama 3.2 (3B) | Local AI inference |
| LLM Runtime | Ollama | Local model server |
| Web Search | Tavily API | Real-time market research |
| HTTP Client | Requests | API communication |
| Memory | In-process list | Conversation context |
| Config | python-dotenv | Environment variables |

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com) installed
- [Tavily API Key](https://tavily.com) (free tier available)

---

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/bizradar-ai.git
cd bizradar-ai
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
TAVILY_API_KEY=your_tavily_key_here
```

> ⚠️ **Never commit your `.env` file to GitHub.**

### 4. Pull the AI Model

```bash
ollama pull llama3.2:3b
```

### 5. Start Ollama

```bash
ollama serve
```

### 6. Run BizRadar AI

```bash
python app.py
```

---

## 💬 Example Session

```
🚀 BizRadar AI Started
Type 'exit' to quit.

You: AI-powered tiffin service for students

🤖 Thinking...

📊 BizRadar AI:

# Startup Analysis

## Idea Summary
An AI-driven meal delivery platform targeting students...

## Market Potential
High demand in tier-1 college cities. Market size estimated...

## Suggested MVP
- User registration & meal preferences
- Daily menu with AI personalization
- Subscription billing system
- Delivery tracking

## Recommended Tech Stack
- Frontend: React
- Backend: FastAPI
- Database: PostgreSQL
- AI Layer: Gemini API

## Risks
- High customer acquisition cost
- Competition from Swiggy/Zomato
- Retention after trial period

## Final Verdict
Viable niche opportunity with strong MVP potential...
```

---

## 🧭 Roadmap

```
✅ Phase 1 — Foundation Agent        (COMPLETE)
   Local LLM + Context Memory + Tools + Prompt Engineering

🔄 Phase 2 — Real Tool Integrations  (IN PROGRESS)
   Web Search + Competitor Discovery + Market Trends

📋 Phase 3 — RAG & Document Intel    (PLANNED)
   PDF Analysis + Vector Search + Knowledge Retrieval

📋 Phase 4 — Multi-Agent System      (PLANNED)
   Market Agent + Competitor Agent + Tech Advisor Agent

📋 Phase 5 — Autonomous Platform     (PLANNED)
   Long-Term Memory + Startup Scoring + Auto Research
```

---

## 🎯 Learning Objectives

This project is built to deeply understand:

- ✅ Prompt Engineering
- ✅ Context Window Management
- ✅ Tool-Augmented AI Agents
- ✅ OOP Architecture for AI Systems
- ✅ Local LLM Deployment
- 🔄 Multi-Agent Orchestration
- 🔄 RAG Pipelines
- 🔄 Production AI Engineering

---

## 🏛️ Design Philosophy

> *"Architecture First. Frameworks Later."*

BizRadar is intentionally built **without LangChain or LlamaIndex** to deeply understand how AI agents work at the foundational level before abstracting with frameworks.

---

## 📜 License

MIT License — feel free to use, modify, and build on this project.

---

<div align="center">

Built as an AI Engineering learning project.

⭐ Star this repo if you found it useful.

---

## 👤 Contact

**Ankush Poonia**

[![GitHub](https://img.shields.io/badge/GitHub-ankush--poonia007-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/ankush-poonia007)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-ankush--poonia007-0A66C2?style=for-the-badge&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ankush-poonia007/)
[![Email](https://img.shields.io/badge/Email-poonaiankush007@gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:poonaiankush007@gmail.com)

</div>