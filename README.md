# 🤖 Multi-Agent Research Assistant

A production-inspired AI system where multiple specialized agents collaborate to **research**, **summarize**, and **fact-check** any question you ask — with a clean Streamlit web UI and full session history.

---

## 📌 What It Does

You type a question. Four AI agents go to work behind the scenes:

```
Your Question
      │
      ▼
┌─────────────────────┐
│   Supervisor Agent  │  ← Decides who works next
└──────────┬──────────┘
           │
    ┌──────▼──────┐
    │  LangGraph  │  ← Manages the pipeline state
    └──────┬──────┘
           │
  ┌────────┼────────────┐
  ▼        ▼            ▼
Researcher  Summarizer  Fact-Checker
(searches)  (condenses) (verifies)
           │
           ▼
      Final Answer + Reliability Score
```

| Agent | What it does |
|-------|-------------|
| **Supervisor** | Reads pipeline state and routes to the next agent |
| **Researcher** | Generates focused search queries and fetches web results |
| **Summarizer** | Condenses raw results into a structured summary |
| **Fact-Checker** | Verifies the summary against sources — scores HIGH / MEDIUM / LOW |

---

## 🖥️ Streamlit UI

The app runs in your browser with two tabs:

### Tab 1 — Research
- Type any research question and click **Research**
- Watch the pipeline progress live — each agent step updates in real time
- See metrics: sources found, reliability score, time taken
- Final answer rendered as markdown with clickable source links
- Full fact-check report in a collapsible section

### Tab 2 — Session History
- Every past research run is saved automatically
- Each session shows: original query, duration, cache hits, reliability verdict
- Full agent timeline with timestamps — see exactly what each agent did
- **Re-run button** — click to prefill the query and run it again instantly

### Sidebar
- Live Redis connection status (green = connected, red = offline)
- Example queries — click any to auto-fill the search box

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|---------|
| Python 3.12 | Core language |
| LangGraph 1.1+ | Agent orchestration & state machine |
| LangChain 1.2+ | LLM abstraction layer |
| langchain-openai | GPT-4o-mini integration |
| langchain-tavily | Web search tool |
| Streamlit | Browser-based UI |
| Redis 7 (Docker) | Session logging & query caching |
| Docker Compose | Service orchestration |
| python-dotenv | Environment & secrets management |
| Pydantic v2 | Input validation & state schema |

---

## 📁 Project Structure

```
multi-agent-research/
├── app.py                   # Streamlit UI (run this)
├── main.py                  # CLI entry point + LangGraph pipeline
├── config.py                # Central settings
├── docker-compose.yml       # Redis service
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variable template
│
├── agents/
│   ├── researcher.py        # Web search agent
│   ├── summarizer.py        # Summarization agent
│   ├── fact_checker.py      # Fact verification agent
│   └── supervisor.py        # Routing controller
│
├── tools/
│   ├── search.py            # Tavily search wrapper
│   └── calculator.py        # Math expression evaluator
│
├── utils/
│   ├── state.py             # ResearchState TypedDict
│   ├── logger.py            # Redis-backed AgentLogger
│   ├── cache.py             # TTL-based query cache
│   ├── validators.py        # Pydantic input validation
│   └── retry.py             # Exponential backoff decorator
│
└── tests/
    └── test_agents.py       # Unit tests (mocked LLM)
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- Docker Desktop installed and running
- An OpenAI API key → [platform.openai.com](https://platform.openai.com)
- A Tavily API key → [app.tavily.com](https://app.tavily.com) *(free — 1,000 searches/month, no credit card)*

---

### 1. Clone the repository

```bash
git clone https://github.com/your-username/multi-agent-research.git
cd multi-agent-research
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Mac / Linux
venv\Scripts\activate           # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in your API keys:

```
OPENAI_API_KEY=your_openai_key_here
TAVILY_API_KEY=your_tavily_key_here
REDIS_HOST=localhost
REDIS_PORT=6379
```

> ⚠️ Never commit your `.env` file. It is already in `.gitignore`.

### 5. Start Redis via Docker

```bash
docker compose up -d
```

Verify Redis is running:

```bash
docker compose ps
# multi-agent-redis should show status: Up
```

### 6. Launch the Streamlit UI

```bash
python -m streamlit run app.py
```

Your browser will open automatically at **http://localhost:8501** 🎉

---

## 🧩 How It Works

### Shared State — The Blackboard Pattern

Every agent communicates through a single shared `ResearchState` dictionary. No agent calls another directly — they only read from and write to this shared state.

```
Initial state  →  { query: "..." , everything else empty }
After Research →  { + search_results, + sources }
After Summary  →  { + summary }
After Check    →  { + fact_check_result, + is_reliable, + final_answer }
```

### LangGraph State Machine

The pipeline is a compiled graph where the Supervisor reads the `next_agent` field after every step and routes accordingly:

```
START → Supervisor → Researcher → Supervisor
                  → Summarizer  → Supervisor
                  → Fact-Checker → Supervisor
                  → END
```

### Redis — Two Jobs

**Logging** — every agent decision is stored as a JSON entry in a Redis list, keyed by session ID with a 48-hour TTL.

**Caching** — search results are cached by an MD5 hash of the query for 24 hours. Identical queries never hit the Tavily API twice.

---

## 🔧 Other Ways to Run

### CLI (without the UI)

```bash
python main.py "What is quantum computing?"

# Interactive prompt
python main.py

# List past sessions
python main.py --sessions

# Verbose debug output
python main.py "Your question" --verbose
```

### Run Tests

```bash
pytest tests/ -v
```

All tests use mocked LLM and API calls — no real API keys needed, runs in seconds.

---

## 🐳 Docker Commands

```bash
# Start Redis
docker compose up -d

# Stop Redis (data is preserved)
docker compose stop

# Check Redis data via CLI
docker exec -it multi-agent-redis redis-cli

# Inside redis-cli:
# KEYS *                      → see all keys
# KEYS session:*              → session logs
# KEYS cache:*                → cached queries
# LRANGE session:ID 0 -1      → read full session log
# TTL session:ID              → seconds until expiry
```

---

## 🏗️ Key Design Patterns

| Pattern | Where | Why |
|---------|-------|-----|
| Blackboard pattern | `ResearchState` | Agents share data without direct coupling |
| Supervisor pattern | `supervisor.py` | Single controller for all routing decisions |
| Immutable state | `**state` spread | Each agent returns a new state, never mutates |
| Single Responsibility | Each agent file | One agent = one job |
| Exponential backoff | `utils/retry.py` | Resilience against flaky API calls |
| TTL caching | `utils/cache.py` | Avoid redundant Tavily API calls |
| Graceful degradation | `utils/logger.py` | App works even if Redis is offline |

---

## 📦 Requirements

```
langgraph>=1.1.0
langchain>=1.2.0
langchain-core>=1.2.0
langchain-openai>=1.1.0
langchain-tavily
redis>=7.1.1
streamlit
python-dotenv>=1.0.0
pydantic>=2.0.0
pytest
```

---

## 🚀 Production Improvements (Roadmap)

- [ ] FastAPI wrapper to expose pipeline as a REST endpoint
- [ ] Async agents using `ainvoke` for concurrent execution
- [ ] GitHub Actions CI/CD pipeline
- [ ] Prometheus metrics and alerting
- [ ] Docker Compose full deployment (app + Redis together)

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙋 Author

Built as a learning project to understand multi-agent AI systems, LangGraph orchestration, and production-ready Python application design.

> ⭐ If this project helped you, consider starring the repository!