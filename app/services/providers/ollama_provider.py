import ollama 
import time
from dataclasses import dataclass
import os
import asyncio
import threading

#Point ollama client at the host machine, not localhost, since the FastAPI server is running inside a Docker container. host.docker.internal is a special DNS name that resolves to the internal IP address of the host machine from within the Docker container, allowing the containerized application to communicate with services running on the host.
OLLAMA_HOST = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

#Create a configured client instance that points to the ollama server running on the host machine, so we can use this client to send request to the ollama server
ollama_client = ollama.Client(host=OLLAMA_HOST)

@dataclass
class BattleResult:
    model_name: str
    response: str
    latency_ms: float
    tokens_per_second: float
    prompt_tokens: int
    response_tokens: int
    error: str = ''

async def run_model(model_name: str, prompt: str) -> BattleResult:
    "Send a prompt to an ollama model and measure performance metrics."
    start_time = time.time()
    try:
        response = await asyncio.to_thread(ollama_client.chat,
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            options={
                "temperature": 0.7, #Control the randomness of the output, with higher values producing more creative responses
                "num_predictions": 512 #max tokens to generate
            }
        )

        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000  # Convert to milliseconds

        response_text = response["message"]["content"]    # Count the number of tokens in the response
        eval_count = response.get("eval_count", 0)    # Get the number of evaluations if available, default to 0
        prompt_eval_count = response.get("prompt_eval_count", 0)    # Get the number of prompt evaluations if available, default to 0
        eval_duration = response.get("eval_duration", 0)    # Get the total evaluation duration if available, default to 0

        tokens_per_second = eval_count / (eval_duration / 1e9) if eval_duration > 0 else 0
        # Calculate tokens per second, ensuring no division by zero

        return BattleResult(
            model_name = model_name,
            response = response_text,
            latency_ms = round(latency_ms, 2),
            tokens_per_second = round(tokens_per_second, 2),
            prompt_tokens = prompt_eval_count,
            response_tokens = eval_count
        )

    except Exception as e:
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000  # Convert to milliseconds
        return BattleResult(
            model_name=model_name,
            response="",
            latency_ms=round((end_time - start_time) * 1000, 2),
            tokens_per_second=0,
            prompt_tokens=0,
            response_tokens=0,
            error=str(e)
        )