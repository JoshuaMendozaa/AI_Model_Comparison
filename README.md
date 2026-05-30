[README.md](https://github.com/user-attachments/files/28168062/README.md)
# ⚔️ AI Model Battle

A real-time benchmarking system where AI models compete head-to-head. Models submit performance metrics live, results are tracked over time, and a live leaderboard updates instantly for every connected viewer.

---

## What It Does

- **AI models (or scripts) submit benchmark scores** — accuracy, latency, tokens/sec, memory usage
- **Scores are stored and tracked over time** — not just the latest, but the full history
- **A live leaderboard ranks models** — updated the moment new data arrives
- **Every connected browser sees updates instantly** — no refreshing, no polling

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Docker Compose                    │
│                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────────┐   │
│  │  :8000   │    │  :5432   │   │    :8086     │    │
│  │          │───▶│          │   │              │   │
│  │  REST +  │    │ Model    │   │  Benchmark   │    │
│  │WebSockets│    │ Metadata │   │   Metrics    │    │
│  └────┬─────┘    └──────────┘   └──────────────┘    │
│       │                                             │
│       │          ┌──────────┐                       │
│       └─────────▶│  Redis   │                      │
│                  │  :6379   │                       │
│                  │  Cache + │                       │
│                  │ Pub/Sub  │                       │
│                  └──────────┘                       │
└─────────────────────────────────────────────────────┘
```

### Why each technology?

| Service | Role | Why not just use Postgres for everything? |
|---|---|---|
| **PostgreSQL** | Model metadata (name, version, creator) | Relational data with clear structure |
| **InfluxDB** | Benchmark scores over time | Purpose-built for time-series — querying trends is trivial |
| **Redis** | Leaderboard cache + pub/sub | Sub-millisecond reads; pub/sub enables multi-server broadcasting |
| **FastAPI** | REST + WebSocket API | Async-native, auto-generated docs, fast |

---

## Project Structure

```
ai-battle/
├── docker-compose.yml        # Orchestrates all 4 services
├── Dockerfile                # Builds the FastAPI container
├── .env                      # Secrets and config (never commit this)
├── requirements.txt          # Python dependencies
└── app/
    ├── main.py               # FastAPI app entry point
    ├── database.py           # PostgreSQL connection + SQLAlchemy setup
    ├── models/
    │   └── ai_model.py       # SQLAlchemy table definition
    ├── routers/
    │   ├── models.py         # REST endpoints for AI model registration
    │   ├── benchmarks.py     # REST endpoints for benchmark submission
    │   └── ws.py             # WebSocket endpoint for live updates
    └── services/
        ├── influx.py         # InfluxDB read/write logic
        ├── redis_service.py  # Cache + pub/sub logic
        └── websocket_manager.py  # Manages active WebSocket connections
```

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Confirm with: `docker --version && docker compose version`

### 1. Clone the repo

```bash
git clone https://github.com/yourusername/ai-battle.git
cd ai-battle
```

### 2. Create your `.env` file

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
```

### 3. Start everything

```bash
docker compose up --build
```

All 4 services start automatically. On first run, PostgreSQL and InfluxDB initialize their databases.

### 4. Verify it's running

```bash
curl http://localhost:8000/health
# → {"status": "online", "message": "AI Battle API is running"}
```

Visit **`http://localhost:8000/docs`** for the interactive API explorer.

---

## API Reference

### Models

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/models/` | Register a new AI model |
| `GET` | `/models/` | List all registered models |
| `GET` | `/models/{id}` | Get a specific model |

**Register a model:**
```bash
curl -X POST http://localhost:8000/models/ \
  -H "Content-Type: application/json" \
  -d '{"name": "GPT-5", "version": "1.0", "creator": "OpenAI", "description": "Benchmark challenger"}'
```

### Benchmarks

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/benchmarks/` | Submit a benchmark score |
| `GET` | `/benchmarks/leaderboard/latest` | Current leaderboard |
| `GET` | `/benchmarks/{model}/{metric}` | Historical scores for a model |

**Valid metrics:** `accuracy` · `latency_ms` · `tokens_per_second` · `memory_mb`

**Submit a benchmark:**
```bash
curl -X POST http://localhost:8000/benchmarks/ \
  -H "Content-Type: application/json" \
  -d '{"model_name": "GPT-5", "metric": "accuracy", "value": 94.2}'
```

**Get leaderboard:**
```bash
curl http://localhost:8000/benchmarks/leaderboard/latest
```

### WebSocket

Connect to receive live leaderboard updates:

```bash
# Install wscat
npm install -g wscat

# Connect
wscat -c ws://localhost:8000/ws/leaderboard
```

On connect you immediately receive the current leaderboard. Every time any model submits a benchmark, all connected clients receive the update instantly — no polling needed.

---

## Running a Live Battle

Submit scores from multiple models and watch the leaderboard update in real time.

**Terminal 1 — watch live:**
```bash
wscat -c ws://localhost:8000/ws/leaderboard
```

**Terminal 2 — simulate a battle:**
```bash
# GPT-5 submits
curl -s -X POST http://localhost:8000/benchmarks/ \
  -H "Content-Type: application/json" \
  -d '{"model_name": "GPT-5", "metric": "accuracy", "value": 94.2}'

# Claude-4 submits
curl -s -X POST http://localhost:8000/benchmarks/ \
  -H "Content-Type: application/json" \
  -d '{"model_name": "Claude-4", "metric": "accuracy", "value": 96.8}'

# GPT-5 fights back
curl -s -X POST http://localhost:8000/benchmarks/ \
  -H "Content-Type: application/json" \
  -d '{"model_name": "GPT-5", "metric": "accuracy", "value": 97.5}'
```

Watch Terminal 1 update after each command.

---

## Key Concepts Demonstrated

**REST API design** — proper use of HTTP methods, status codes, and Pydantic validation

**Async Python** — all endpoints and DB calls are `async`, enabling high concurrency without blocking

**Relational vs time-series databases** — PostgreSQL for structured metadata, InfluxDB for metrics that accumulate over time

**Caching strategy** — Redis cache with TTL and write-through invalidation; leaderboard served in <1ms on cache hit vs 50-200ms from InfluxDB

**WebSocket broadcasting** — single `ConnectionManager` instance shared across routes; broadcasts to all connected clients on every new submission

**Docker Compose** — all services defined, networked, and orchestrated in one file; `docker compose up` is the only command needed to run the full stack

---

## Stopping and Resetting

```bash
# Stop all containers
docker compose down

# Stop and delete all data (fresh start)
docker compose down -v
```

---

## What's Next

- [ ] `simulate.py` — script to auto-submit benchmark scores from multiple models
- [ ] Analytics layer — pandas + scikit-learn trend analysis and forecasting endpoints
- [ ] Frontend dashboard — live leaderboard UI with charts

---

## License

MIT
