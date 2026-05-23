curl -s -X POST http://localhost:8000/benchmarks/ \
  -H "Content-Type: application/json" \
  -d '{"model_name": "GPT-5", "metric": "accuracy", "value": 94.2}'

curl -s -X POST http://localhost:8000/benchmarks/ \
  -H "Content-Type: application/json" \
  -d '{"model_name": "Claude-4", "metric": "accuracy", "value": 96.8}'

curl -s http://localhost:8000/benchmarks/leaderboard/latest