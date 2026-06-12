import ollama
import json
import re
import os


OLLAMA_HOST = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
client = ollama.Client(host=OLLAMA_HOST)

JUDGE_PROMPT = """You are an expert AI evaluator. Score the following response to this prompt.

PROMPT: {prompt}

RESPONSE: {response}

Score the response on these 5 dimensions, each from 0 to 10:
1. Correctness: Is the answer factually/logically correct?
2. Reasoning: Does it show clear step-by-step thinking?
3. Completeness: Does it fully address the prompt?
4. Conciseness: Is it free of unnecessary padding?
5. Coherence: Is it well structured and easy to follow?

You MUST respond with ONLY a JSON object. No thinking tags, no explanation, no extra text.
Respond with ONLY this exact format:
{{"correctness": 0, "reasoning": 0, "completeness": 0, "conciseness": 0, "coherence": 0, "overall": 0, "summary": "one sentence"}}"""

def judge_response(prompt: str, response: str, judge: str) -> dict:
    """judge a model response on 5 research dimensions"""

    if not response or len(response.strip()) < 10:
        return _default_score("No response provided")

    try:
        result = client.chat(
            model=judge,
            messages=[{
                "role": "user",
                "content": JUDGE_PROMPT.format(
                    prompt=prompt,
                    response=response[:2000]  # cap at 2000 chars
                )
            }],
            options={"temperature": 0.1}  # low temp for consistent scoring
        )

        content = result["message"]["content"]
        print(f"Raw judge response: {content}")
        content = re.sub(r'<tool_call>.*?</tool_call>', '', content, flags=re.DOTALL).strip()  # remove any <tool_call> tags if model adds them

        # Extract JSON even if model adds extra text
        json_match = re.search(r'\{.*\}', content, re.DOTALL)   #use regex to extract the JSON object from the model's response. 
        if json_match:
            scores = json.loads(json_match.group())
            required =  ["correctness", "reasoning", "completeness", "conciseness", "coherence"]
            # Ensure overall is weighted average if not provided correctly
            if all(k in scores for k in required):
                if "overall" not in scores:
                    avg = sum(scores[k] for k in required) / len(required)
                    scores["overall"] = round(avg * 10, 1)
                print(f"Judge scores: {scores}")
                return scores
        return _default_score("Model did not return valid JSON scores")

    except Exception as e:
        print(f"Judge error: {e}")

    return {
        "correctness": 5,
        "reasoning": 5,
        "completeness": 5,
        "conciseness": 5,
        "coherence": 5,
        "overall": 50,
        "summary": "Scoring unavailable"
    }

def _default_score(reason: str) -> dict:
    return {
        "correctness": 0,
        "reasoning": 0,
        "completeness": 0,
        "conciseness": 0,
        "coherence": 0,
        "overall": 0,
        "summary": reason
    }