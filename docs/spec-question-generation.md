# Spec: question_generation, a Deep Module that returns questions inside a time budget

Sub-issue of "Design Document — Eduardo Migueis". Draft to post with `gh issue create`.

## What it hides
Threads, the cap on concurrent LLM calls, the per-call timeout, the retry on invalid output, and the logging of failures. Callers do not know the LLM is slow, flaky or called in parallel.

## What it promises
`generate_questions(prompts, llm, parse, *, max_concurrency=4, call_timeout=30.0, max_attempts=3) -> list[dict | None]`

- One result per prompt, **in the order of the prompts**.
- At most `max_concurrency` LLM calls in flight.
- Output that `parse` rejects with `ValueError` is retried, up to `max_attempts` attempts per prompt.

## Failures
- A prompt that never parses, times out, or whose call raises gives `None` at its position. The function **never raises** because of one prompt; the other questions are still returned.
- A call exceeding `call_timeout` is abandoned: the caller gets `None` at that position after about `call_timeout` seconds. (The abandoned thread ends when the LLM does.)

## Acceptance criterion (my number)
**10 questions are returned in at most 60 s when every LLM call takes 10 s** (tests run it at 1/50 scale: 10 calls of 0.2 s in under 1.2 s; the sequential code takes 2.0 s and fails).

## Out of scope
Wiring `generate_mixed_test` and `POST /session/evaluation` to this module (next step); making the endpoint non-blocking for other users; token limits and the Mistral rate limit (Limits page not yet read).

## Tests (tests/test_question_generation.py)
1. Slow fake LLM, 10 prompts, budget respected, order kept.
2. Invalid output once, then valid: retried, one extra call.
3. Never parses: `None`, no exception.
4. Hung call: `None` within the timeout.
