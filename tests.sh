#!/bin/bash

echo "--- Register a model ---"
curl -s -X POST http://localhost:8000/models/ \
  -H "Content-Type: application/json" \
  -d '{"name": "GPT-5", "version": "1.0", "creator": "OpenAI", "description": "Benchmark challenger"}'

echo ""
echo "--- List all models ---"
curl -s http://localhost:8000/models/

echo ""
echo "--- Get model by ID ---"
curl -s http://localhost:8000/models/1

echo ""
echo "--- Health check ---"
curl -s http://localhost:8000/health