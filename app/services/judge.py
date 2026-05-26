import ollama
import json
import re

JUDGE_MODEL = "deepseek/judge:latest"

JUDGE_PROMPT = """You are an expert AI evaluator. Score the following response to this prompt.

PROMPT: {prompt}

RESPONSE: {response}

Score the response on these 5 dimensions, each from 0 to 10:
1. Correctness: Is the answer factually/logically correct?
2. Reasoning: Does it show clear step-by-step thinking?
3. Completeness: Does it fully address the prompt?
4. Conciseness: Is it free of unnecessary padding?
5. Coherence: Is it well structured and easy to follow?

Respond ONLY with a JSON object in this exact format, nothing else:
{{
  "correctness": <0-10>,
  "reasoning": <0-10>,
  "completeness": <0-10>,
  "conciseness": <0-10>,
  "coherence": <0-10>,
  "overall": <0-100>,
  "summary": "<one sentence explaining the score>"
}}"""

def judge_response(prompt: str, response: str) -> dict:
    """Use deepseek/judge to judge a model response on 5 research dimensions"""

    if not response or len(response.strip()) < 10:
        return {
            "correctness": 0,
            "reasoning": 0,
            "completeness": 0,
            "conciseness": 0,
            "coherence": 0,
            "overall": 0,
            "summary": "No response provided"
        }

    try:
        result = ollama.chat(
            model=JUDGE_MODEL,
            messages=[{
                "role": "user",
                "content": JUDGE_PROMPT.format(
                    prompt=prompt,
                    response=response[:2000]  # cap at 2000 chars
                )
            }],
            options={"temperature": 0.1}  # low temp for consistent scoring
        )

        content = result["message"]["content"].strip()

        # Extract JSON even if model adds extra text
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            scores = json.loads(json_match.group())
            # Ensure overall is weighted average if not provided correctly
            if "overall" not in scores:
                dims = ["correctness", "reasoning", "completeness", "conciseness", "coherence"]
                avg = sum(scores.get(d, 0) for d in dims) / len(dims)
                scores["overall"] = round(avg * 10, 1)
            return scores

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