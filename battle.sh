curl -s -X POST http://localhost:8000/battle/start \
  -H "Content-Type: application/json" \
  -d '{
    "category": "reasoning",
    "models": ["llama3.2", "mistral"]
  }'