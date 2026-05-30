import json
import re

#unit test for judge.py

def test_judge_json_extraction():
    """The judge should extract JSON even when wrapped in thinking tags"""
    #Simulate a DeepSeek response with thinking tags
    raw_response = """<think>
    Let me evaluate this carefully, The answer is correct.
    </think>
    
    {"correctness": 9, "reasoning": 8, "completeness": 8, "conciseness": 7, "coherence": 8}"""

    #Strip think tags (logic similar to judge.py)
    content = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL).strip()
    json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)

    assert json_match is not None
    scores = json.loads(json_match.group())
    assert scores["correctness"] == 9
    assert len(scores) == 5

def test_overall_score_calc():
    """Overall should be the average of 5 dimensions, scaled to 0-100"""
    scores = {
        "correctness": 10,
        "reasoning": 10, 
        "completeness": 10,
        "conciseness": 10,
        "coherence": 10
    }
    required = ["correctness", "reasoning", "completeness", "conciseness", "coherence"]

    avg = sum(scores[k] for k in required) / len(required)
    overall = round(avg * 10, 1)

    assert overall == 100.0

def test_overall_score_partial():
    """A mixed-score response should compoute the correct average"""
    scores = {
         "correctness": 4,
        "reasoning": 8, 
        "completeness": 9,
        "conciseness": 9,
        "coherence": 9
    }

    required = ["correctness", "reasoning", "completeness", "conciseness", "coherence"]

    avg = sum(scores[k] for k in required) / len(required)
    overall = round(avg * 10, 1)

    assert overall == 78.0