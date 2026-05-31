# ⚔️ AI Model Battle

![CI](https://github.com/JoshuaMendozaa/AI_Model_Comparison/actions/workflows/ci.yml/badge.svg)

A real-time benchmarking platform that pits LLMs against each other on standardized stress tests — measuring speed, quality, and reasoning under pressure. Models battle head-to-head on identical prompts while a judge model scores responses using research-backed evaluation criteria.

Built with **FastAPI · PostgreSQL · InfluxDB · Redis · WebSockets · Docker · Ollama**

---

## How It Works

1. **Pick a category** — reasoning, coding, knowledge, or creative
2. **Choose your fighters** — any Ollama-supported model (DeepSeek, Llama, Mistral, Gemma, Phi, Qwen, and more)
3. **Same prompt fires to all models simultaneously** — async concurrency, not sequential
4. **A judge model scores each response** on correctness, reasoning, completeness, conciseness, and coherence (0-100 scale)
5. **Results stream live** to all connected clients via WebSocket — no polling, no refreshing

```
POST /battle/start
  { "category": "reasoning", "models": ["llama3.2", "mistral"] }

Same prompt ──▶ llama3.2  ──▶ response + latency
             ──▶ mistral   ──▶ response + latency
                                    │
                              Judge (deepseek-r1)
                              scores both on 5 dimensions
                                    │
                              InfluxDB stores metrics
                              Redis caches leaderboard
                              WebSocket broadcasts live
```

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Docker Compose                            │
│                                                                  │
│  ┌───────────────┐     ┌────────────┐     ┌──────────────────┐  │
│  │    FastAPI     │────▶│ PostgreSQL │     │     InfluxDB     │  │
│  │    :8000       │     │   :5432    │     │      :8086       │  │
│  │                │     │            │     │                  │  │
│  │  REST API      │     │  Model     │     │   Benchmark      │  │
│  │  WebSockets    │     │  metadata  │     │   metrics over   │  │
│  │  Battle engine │     │  (who)     │     │   time (how)     │  │
│  └──────┬─────────┘     └────────────┘     └──────────────────┘  │
│         │                                                        │
│         │               ┌────────────┐                           │
│         └──────────────▶│   Redis    │                           │
│                         │   :6379    │                           │
│                         │            │                           │
│                         │  Cache +   │                           │
│                         │  Pub/Sub   │                           │
│                         └────────────┘                           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  Ollama (host)     │
                    │  :11434            │
                    │                    │
                    │  LLM inference     │
                    │  deepseek-r1       │
                    │  llama3.2          │
                    │  mistral           │
                    └────────────────────┘
```

### Why This Stack?

| Service | Purpose | Why not just Postgres? |
|---|---|---|
| **PostgreSQL** | Model metadata — name, version, creator | Relational data with fixed schema |
| **InfluxDB** | Benchmark scores over time | Purpose-built for time-series queries like "average latency over the last hour, grouped by 5-minute intervals" |
| **Redis** | Leaderboard cache + pub/sub messaging | Serves cached leaderboard in <1ms instead of querying InfluxDB every request; pub/sub enables multi-server broadcasting |
| **Ollama** | Local LLM inference | Runs any open-source model locally — no API keys, no cost, no internet required |

---

## Project Structure

```
├── .github/workflows/ci.yml       CI/CD pipeline — builds and tests on every push
├── docker-compose.yml              Orchestrates all 4 services
├── Dockerfile                      Builds the FastAPI container image
├── requirements.txt                Python dependencies
├── pytest.ini                      Test configuration
├── tests/
│   ├── conftest.py                 Pytest path setup
│   ├── test_health.py              API endpoint tests
│   ├── test_judge.py               Judge logic unit tests
│   └── test_battle_validation.py   Input validation tests
└── app/
    ├── main.py                     FastAPI entry point + startup logic
    ├── database.py                 Async PostgreSQL connection (SQLAlchemy)
    ├── models/
    │   └── ai_model.py             SQLAlchemy ORM table definition
    ├── routers/
    │   ├── models.py               CRUD endpoints for AI model registration
    │   ├── benchmarks.py           Benchmark submission + leaderboard
    │   ├── battle.py               Battle orchestration engine
    │   └── ws.py                   WebSocket endpoint for live updates
    ├── services/
    │   ├── influx.py               InfluxDB time-series read/write
    │   ├── redis_service.py        Cache (TTL + invalidation) + pub/sub
    │   ├── websocket_manager.py    Connection manager for broadcast
    │   ├── judge.py                LLM-as-a-Judge scoring with 5 dimensions
    │   └── providers/
    │       └── ollama_provider.py  Ollama client adapter
    └── prompts/
        └── prompts.json            Curated stress prompts by category
```

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — for the containerized backend
- [Ollama](https://ollama.com) — for local LLM inference

### 1. Clone and configure

```bash
git clone https://github.com/JoshuaMendozaa/AI_Model_Comparison.git
cd AI_Model_Comparison
```

Create a `.env` file:

```env
POSTGRES_USER=admin
POSTGRES_PASSWORD=secret
POSTGRES_DB=ai_battle

INFLUXDB_USER=admin
INFLUXDB_PASSWORD=secretpassword
INFLUXDB_ORG=ai-battle
INFLUXDB_BUCKET=benchmarks
INFLUXDB_TOKEN=my-super-secret-token

REDIS_URL=redis://redis:6379
OLLAMA_BASE_URL=http://host.docker.internal:11434
JUDGE_MODEL=deepseek-r1
```

### 2. Pull models

```bash
ollama pull llama3.2
ollama pull mistral
ollama pull deepseek-r1
```

### 3. Start everything

```bash
docker compose up --build
```

### 4. Verify

```bash
curl http://localhost:8000/health
# {"status": "online", "message": "AI Battle API is running"}

curl http://localhost:8000/battle/models/available
# {"models": ["llama3.2:latest", "mistral:latest", "deepseek-r1:latest"], "judge": "deepseek-r1"}
```

Visit `http://localhost:8000/docs` for the full interactive API explorer.

---

## Running a Battle

### Start a battle

```bash
curl -X POST http://localhost:8000/battle/start \
  -H "Content-Type: application/json" \
  -d '{"category": "reasoning", "models": ["llama3.2", "mistral"]}'
```

### Watch live via WebSocket

```bash
# Install wscat: npm install -g wscat
wscat -c ws://localhost:8000/ws/leaderboard
```

Every benchmark submission broadcasts instantly to all connected clients — no polling.

### Sample battle output

```json
{
  "category": "reasoning",
  "prompt": "If it takes 5 machines 5 minutes to make 5 widgets...",
  "results": [
    {
      "model": "mistral",
      "latency_ms": 2706.89,
      "tokens_per_second": 141.65,
      "scores": {
        "correctness": 10,
        "reasoning": 10,
        "completeness": 10,
        "overall": 100.0,
        "summary": "Logically sound with correct reasoning"
      }
    },
    {
      "model": "llama3.2",
      "latency_ms": 2222.67,
      "tokens_per_second": 270.58,
      "scores": {
        "correctness": 4,
        "reasoning": 8,
        "overall": 78.0,
        "summary": "Faster but reached incorrect conclusion"
      }
    }
  ],
  "winner": "mistral"
}
```

---

## API Reference

### Models

| Method | Endpoint | Description |
|---|---|---|
| POST | `/models/` | Register a new AI model |
| GET | `/models/` | List all registered models |
| GET | `/models/{id}` | Get a specific model |

### Benchmarks

| Method | Endpoint | Description |
|---|---|---|
| POST | `/benchmarks/` | Submit a benchmark score |
| GET | `/benchmarks/leaderboard/latest` | Current leaderboard (Redis-cached) |
| GET | `/benchmarks/{model}/{metric}?hours=1` | Historical scores |

### Battle

| Method | Endpoint | Description |
|---|---|---|
| POST | `/battle/start` | Start a battle between models |
| GET | `/battle/models/available` | List Ollama models available for battle |
| GET | `/battle/prompts/{category}` | Preview stress prompts by category |

### WebSocket

| Endpoint | Description |
|---|---|
| `ws://localhost:8000/ws/leaderboard` | Live leaderboard updates on every benchmark |

**Valid metrics:** `accuracy` · `latency_ms` · `tokens_per_second` · `memory_mb`

**Valid categories:** `reasoning` · `coding` · `knowledge` · `creative`

---

## Testing

```bash
# Run all tests
docker compose exec api pytest -v

# Run specific test file
docker compose exec api pytest tests/test_judge.py -v
```

Tests cover API endpoint validation, judge scoring logic, and health checks. CI runs automatically on every push via GitHub Actions.

---

## Design Decisions

**Why two databases?** PostgreSQL stores structured model metadata (name, version, creator) — data that rarely changes and has clear relationships. InfluxDB stores benchmark scores — time-series data that accumulates rapidly and needs temporal queries like "average latency over the last hour." Using the right database for each data type is a core data engineering principle.

**Why Redis caching?** Without caching, every leaderboard request queries InfluxDB (50-200ms). With Redis, cached responses serve in <1ms. The cache uses a write-through strategy with a 30-second TTL — invalidated immediately on new data, auto-expires as a safety net.

**Why asyncio.gather for battles?** Models run concurrently, not sequentially. If each model takes 60 seconds, a 3-model battle takes ~60 seconds total instead of 180. `asyncio.to_thread` moves the synchronous Ollama calls off the main event loop so the server stays responsive during battles.

**Why LLM-as-a-Judge?** Based on the MT-Bench research approach (Zheng et al., 2023). A stronger model evaluates weaker ones on 5 research-standard dimensions. The overall score is computed deterministically in Python — never trusting an LLM for arithmetic. The judge is configurable via environment variable for easy swapping.

**Why a pluggable provider pattern?** Every provider implements the same interface. Adding a new model source (OpenAI, Anthropic, HuggingFace) requires one new file with zero changes to the battle logic. This is the adapter pattern — one of the most practical design patterns in production systems.

---

## Stopping and Resetting

```bash
# Stop all containers
docker compose down

# Stop and delete all data (fresh start)
docker compose down -v
```

---

## Future Enhancements

- [ ] Analytics layer — pandas + scikit-learn trend analysis and performance forecasting
- [ ] Frontend dashboard — live leaderboard with charts and battle control panel
- [ ] Sandboxed code execution — run and test LLM-generated code automatically
- [ ] API provider support — plug in OpenAI, Anthropic, and DeepSeek alongside Ollama

---

## License

MIT