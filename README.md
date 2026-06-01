<div align="center">

# 🧠 BizRadar AI

### AI-Powered Startup Intelligence & Business Analysis Agent

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Groq](https://img.shields.io/badge/Groq-LPU%20Inference-F55036?style=for-the-badge&logo=groq&logoColor=white)](https://groq.com)
[![Llama](https://img.shields.io/badge/Llama-3.3%2070B-blueviolet?style=for-the-badge)](https://groq.com/llama3)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Flash-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev)
[![Tavily](https://img.shields.io/badge/Tavily-Search%20API-orange?style=for-the-badge)](https://tavily.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Status](https://img.shields.io/badge/Status-V2%20Active-brightgreen?style=for-the-badge)]()

**Transform any startup idea into a structured business intelligence report — powered by Groq LPU inference, ReAct agent loop, parallel tool execution, and real-time web search.**

[Getting Started](#-getting-started) • [Features](#-features) • [Architecture](#-architecture) • [Roadmap](#-roadmap)

---

</div>

## 🎯 What Is BizRadar AI?

BizRadar AI is a **ReAct-pattern AI agent** that takes a raw startup idea and returns a full structured analysis — covering market potential, competitors, MVP features, tech stack recommendations, and risk assessment.

> **Example Input:** `"AI-powered tiffin service for students"`
>
> **Output:** A complete startup analysis report with cited sources, market insights, MVP suggestions, tech stack, and risk evaluation.

Powered by **Groq's LPU inference engine** for ultra-fast responses, with tools executed in **parallel via ThreadPoolExecutor** and market data sourced live via **Tavily Search API**.

---

## ✨ Features

| Feature | Description | Status |
|---|---|---|
| ⚡ Groq LPU Inference | Ultra-fast token generation via purpose-built LPUs | ✅ Live |
| 🔁 ReAct Agent Loop | LLM reasons → calls tools → observes → loops to final answer | ✅ Live |
| 🧵 Parallel Tool Execution | Tools run simultaneously via ThreadPoolExecutor | ✅ Live |
| 🧠 Context Memory | Remembers last 6 conversation turns | ✅ Live |
| 🔍 Real-Time Web Search | Market analysis via Tavily API | ✅ Live |
| 📊 Startup Analysis | Structured business intelligence report with cited sources | ✅ Live |
| 💡 MVP Recommendations | Core feature suggestions via Gemini 2.5 Flash | ✅ Live |
| 🏗️ Tech Stack Advisor | CTO-level stack recommendations via Gemini 2.5 Flash | ✅ Live |
| ⚠️ Risk Analysis | Identifies fatal flaws and mitigation strategies | ✅ Live |
| 🛠️ Tool Schema Layer | Structured tool descriptions for LLM tool-calling | ✅ Live |
| 📚 RAG Pipeline | Document & vector search integration | 🔄 Planned |
| 🤝 Multi-Agent System | Specialized agents working in parallel | 🔄 Planned |

---

## 📁 Project Structure

```
bizradar-ai/
│
├── 🤖 agent.py               # ReAct agent — Groq LLM + parallel tool execution loop
├── 🖥️  app.py                 # CLI entry point
├── 🧠 context_manager.py     # Conversation memory (last 6 turns)
├── 🛠️  tools.py               # Tool layer — Tavily search + Gemini analysis
├── 📋 tools_description.py   # Tool schemas for LLM tool-calling (JSON format)
├── 📝 prompts.py             # System prompt + output format templates
│
├── 📦 requirements.txt       # Python dependencies
├── 🔒 .env                   # API keys (never commit this)
├── 🚫 .gitignore             # Ignores .env and cache files
├── 📖 README.md              # Project overview and getting started
├── 🧭 ROADMAP.md             # Phase-by-phase build and learning path
├── 🏗️  ARCHITECTURE.md        # Deep dive into every design decision
└── 📓 LEARNING_LOG.md        # Personal learning tracker and mistake log
```

---
## ReAct Pattern

![ReAct Image](/react_pattern_architecture.svg)
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
┌─────────────────────────────────────────────────────┐
│              ReAct AGENT LOOP (agent.py)            │
│                                                     │
│  ┌──────────────┐     ┌───────────────────────────┐ │
│  │   Context    │     │      Groq LLM             │ │
│  │   Manager    │────▶│   Llama 3.3 70B           │ │
│  │  Last 6 msgs │     │   Reason → Act → Observe  │ │
│  └──────────────┘     └────────────┬──────────────┘ │
│                                    │                 │
│                          tool_calls detected?        │
│                                    │                 │
│                    ┌───────────────▼──────────────┐  │
│                    │  ThreadPoolExecutor           │  │
│                    │  (Parallel Execution)         │  │
│                    │                              │  │
│                    │ ┌────────────────────────┐   │  │
│                    │ │ analyze_market()        │   │  │
│                    │ │ search_knowledge_base() │   │  │
│                    │ │ suggest_mvp()           │   │  │
│                    │ │ recommend_tech_stack()  │   │  │
│                    │ │ risk_analysis()         │   │  │
│                    │ └────────────────────────┘   │  │
│                    │  Tavily API + Gemini 2.5 Flash│  │
│                    └───────────────┬──────────────┘  │
│                                    │                 │
│                          results appended to messages│
│                                    │                 │
│                    ┌───────────────▼──────────────┐  │
│                    │  Loop back to Groq LLM        │  │
│                    │  until no tool_calls remain   │  │
│                    └───────────────┬──────────────┘  │
└────────────────────────────────────┼─────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────┐
│         STRUCTURED STARTUP REPORT           │
│                                             │
│  # Idea Summary    # Market Potential       │
│  # Competitors     # Suggested MVP          │
│  # Tech Stack      # Risks                  │
│  # Final Verdict   # Cited Sources          │
└─────────────────────────────────────────────┘
```

---

## ⚙️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| Language | Python 3.10+ | Core runtime |
| LLM Inference | Groq — Llama 3.3 70B | Ultra-fast ReAct reasoning via LPU |
| Analysis Tools | Gemini 2.5 Flash | MVP, tech stack, risk generation |
| Web Search | Tavily API | Real-time market research + citations |
| Parallel Execution | ThreadPoolExecutor | Simultaneous tool execution |
| Memory | In-process list | Conversation context (last 6 turns) |
| Tool Schemas | JSON function definitions | LLM tool-calling interface |
| Config | python-dotenv | Environment variable management |

---

## 🔁 ReAct Agent Pattern

BizRadar V2 implements the **ReAct (Reasoning + Acting)** pattern:

```
REASON  → What do I need to find out?
ACT     → Call the right tool(s) in parallel
OBSERVE → Read tool results
REASON  → Do I have enough information?
ACT     → Call more tools if needed
...
ANSWER  → Generate final structured report
```

The LLM decides **which tools to call, when, and with what inputs** — no hardcoded tool execution order.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Groq API Key](https://console.groq.com) (free tier available)
- [Tavily API Key](https://tavily.com) (free tier available)
- [Gemini API Key](https://aistudio.google.com) (free tier available)

---

### 1. Clone the Repository

```bash
git clone https://github.com/ankush-poonia007/STARTUP-AI-AGENT.git
cd STARTUP-AI-AGENT
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root:

```bash
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here
GEMINI_API_KEY=your_gemini_key_here
```

> ⚠️ **Never commit your `.env` file to GitHub.**

### 4. Run BizRadar AI

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
🔧 Calling tool: analyze_market
🔧 Calling tool: search_knowledge_base
🔧 Calling tool: suggest_mvp
🔧 Calling tool: recommend_tech_stack
🔧 Calling tool: risk_analysis

📊 BizRadar AI:

# Startup Analysis

## Idea Summary
An AI-driven meal delivery platform targeting students...

## Market Potential
High demand in tier-1 college cities. [Source: economictimes.com]

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
   Local LLM (Ollama) + Context Memory + Tools + Prompt Engineering

✅ Phase 2 — Real Tool Integrations  (COMPLETE)
   Groq LPU + ReAct Loop + Parallel Execution + Gemini Tools + Tavily Search

📋 Phase 3 — RAG & Document Intel    (PLANNED)
   PDF Analysis + Vector Search + Knowledge Retrieval

📋 Phase 4 — Multi-Agent System      (PLANNED)
   Market Agent + Competitor Agent + Tech Advisor Agent

📋 Phase 5 — Autonomous Platform     (PLANNED)
   Long-Term Memory + Startup Scoring + Auto Research Pipelines
```

---

## 🎯 Learning Objectives

This project is built to deeply understand:

- ✅ Prompt Engineering
- ✅ Context Window Management
- ✅ Tool-Augmented AI Agents
- ✅ ReAct Agent Pattern
- ✅ Parallel Tool Execution
- ✅ OOP Architecture for AI Systems
- ✅ LLM Provider Integration (Groq, Gemini)
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