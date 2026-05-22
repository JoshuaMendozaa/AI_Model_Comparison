#!/bin/bash

echo "--- Register models ---"
curl -s -X POST http://localhost:8000/models/ \
  -H "Content-Type: application/json" \
  -d '{"name": "GPT-5", "version": "1.0", "creator": "OpenAI", "description": "Benchmark challenger"}'

curl -s -X POST http://localhost:8000/models/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Claude-4", "version": "1.0", "creator": "Anthropic", "description": "Benchmark challenger"}'

echo ""
echo "--- Submit benchmarks ---"
curl -s -X POST http://localhost:8000/benchmarks/ \
  -H "Content-Type: application/json" \
  -d '{"model_name": "GPT-5", "metric": "accuracy", "value": 94.2}'

curl -s -X POST http://localhost:8000/benchmarks/ \
  -H "Content-Type: application/json" \
  -d '{"model_name": "Claude-4", "metric": "accuracy", "value": 96.8}'

curl -s -X POST http://localhost:8000/benchmarks/ \
  -H "Content-Type: application/json" \
  -d '{"model_name": "GPT-5", "metric": "latency_ms", "value": 342.5}'

curl -s -X POST http://localhost:8000/benchmarks/ \
  -H "Content-Type: application/json" \
  -d '{"model_name": "Claude-4", "metric": "latency_ms", "value": 289.1}'

echo ""
echo "--- Query benchmarks ---"
curl -s http://localhost:8000/benchmarks/GPT-5/accuracy

echo ""
echo "--- Leaderboard ---"
curl -s http://localhost:8000/benchmarks/leaderboard/latest