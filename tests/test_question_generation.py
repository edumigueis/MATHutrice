"""Acceptance tests for mathutrice.question_generation (Spec: 10 questions in <= 60 s).

Time is scaled by 1/50 so the suite stays fast: a "10 s" LLM call sleeps 0.2 s,
and the 60 s budget becomes 1.2 s. Sequential generation of 10 such calls takes
2.0 s and fails; four at a time takes 0.6 s.
"""

import json
import threading
import time

from mathutrice.question_generation import generate_questions

SCALE = 1 / 50
CALL_SECONDS = 10 * SCALE
BUDGET_SECONDS = 60 * SCALE


def slow_llm(prompt: str) -> str:
    time.sleep(CALL_SECONDS)
    return json.dumps({"question": prompt})


def parse(raw: str) -> dict:
    data = json.loads(raw)  # json.JSONDecodeError is a ValueError
    if "question" not in data:
        raise ValueError("no question")
    return data


def test_ten_questions_from_a_slow_llm_fit_the_budget():
    prompts = [f"q{i}" for i in range(10)]

    start = time.monotonic()
    questions = generate_questions(prompts, slow_llm, parse)
    elapsed = time.monotonic() - start

    assert [q["question"] for q in questions] == prompts
    assert elapsed < BUDGET_SECONDS


def test_invalid_output_is_retried_then_succeeds():
    calls = {"n": 0}

    def flaky_llm(prompt: str) -> str:
        calls["n"] += 1
        return "not json" if calls["n"] == 1 else json.dumps({"question": prompt})

    questions = generate_questions(["q0"], flaky_llm, parse, max_attempts=3)

    assert questions == [{"question": "q0"}]
    assert calls["n"] == 2


def test_a_question_that_never_parses_is_none_not_an_exception():
    questions = generate_questions(
        ["q0", "q1"], lambda p: "not json", parse, max_attempts=3
    )

    assert questions == [None, None]


def test_a_hung_call_gives_none_within_the_timeout():
    release = threading.Event()

    def hung_llm(prompt: str) -> str:
        release.wait(5)
        return json.dumps({"question": prompt})

    start = time.monotonic()
    try:
        questions = generate_questions(["q0"], hung_llm, parse, call_timeout=0.2)
        elapsed = time.monotonic() - start
    finally:
        release.set()

    assert questions == [None]
    assert elapsed < 1.0
