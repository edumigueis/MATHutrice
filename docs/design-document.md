# Design Document v1 — Eduardo Migueis (MATHutrice)

v0 is kept in `design-document-v0.md` (post it as a comment on the issue). v1 gives each non-functional requirement a number and its source.

Draft kept in the fork. To publish: open it as a public issue on EPF-MDE/MATHutrice titled
"Design Document — Eduardo Migueis", link that issue from the README, and post the questions
on EPF-MDE/MATHutrice#40.

## 1. Questions for the product owner

Left open by the Project Overview. **A** = answer to obtain from the Instructor; **Assumption** is what I design with until then.
Type: F = functional, NF = non-functional.

| # | Question | Type | Assumption |
|---|----------|------|------------|
| 1 | How long may a student wait for an evaluation test before the page feels broken? | NF | 60 s typical (n=10), with a visible progress state |
| 2 | How many students evaluate at the same time (a class, a promotion, the Moodle deadline night)? | NF | 30 concurrent in a practical session, 300 enrolled |
| 3 | Must a question the student has seen be reproducible (same test again, review after the fact)? | F | No: generated on the fly, only scores are stored |
| 4 | Who is allowed to see a student's progression: the student, the teacher of the class, admins? | F | Student + Teacher + Admin, via roles already in the app |
| 5 | How wrong may a generated question be? Is a teacher review required before a question reaches students? | F/NF | No review; QCM answers are SymPy-checked where possible |
| 6 | Is the LLM provider fixed (Mistral free tier, or the EPF gateway), and may student answers leave the EPF? | NF | Any OpenAI-compatible endpoint (ADR-0002); free-tier data may be used for training, so no real data |
| 7 | What is the retention of conversations and answers? | NF | Conversations 24 h (as implemented by `cleanup_old_conversations`), progressions kept |
| 8 | Must the app work offline of the LLM (degraded mode) when the endpoint is down or rate-limited? | NF | No: show an error, retry later |
| 9 | Which languages must the UI and the generated questions support? | F | French only |
| 10 | Is the Moodle/EPF referentiel (notions, competences, levels) fixed for the year? | F | Fixed; lives in `mathutrice/referentiel.py` and is seeded into the database |

## 2. The number: how long can a student wait for an evaluation test?

### Facts, with the file each comes from (read 2 November 2026)

- `POST /session/evaluation` — `mathutrice/app.py:2130` (`evaluation_endpoint`). `EvaluationRequest.n_questions` defaults to 10 (`app.py:910-912`); the page sends `evalNQuestions` (`templates/session.html:1551`); the endpoint clamps it to **5…20** (`app.py`, `n = max(5, min(20, ...))`).
- The test is split 20 % basique / 50 % solide / 30 % expert, and each part into 50 % QCM / 30 % QRO / rest step-by-step. For n=10 that is 2+5+3 groups; counting rounding: **5 QCM + 4 QRO + 1 step-by-step = 10 generation calls**. For n=20: 20 calls. (Rounding is Python's banker's rounding; the count is n, give or take 1 with `max(1, …)`.)
- Each question is **one LLM call** — `call_mistral` in `fonctions_python/base_generator.py:67-100`, via `generate_qcm_test` / `generate_qro_test` / `generate_steps_test`, which loop over the questions **one after the other**. No threads, no `asyncio.gather`: the calls are **sequential**.
- Retries: `MAX_RETRIES = 3` (`base_generator.py:35`), but only when the answer is not valid JSON (`ValueError`). So up to **3 calls per question**: n=10 → 10…30 calls, n=20 → 20…60.
- QCM verification (`verifier.py`, SymPy) makes no LLM call. Only QRO *correction* (`qro_generator.py:154`) calls the LLM, and not on this endpoint.
- Timeout: none set in `mathutrice/llm_client.py`, so the OpenAI SDK defaults apply: **600 s per request**, with **2 automatic retries** on 429/5xx/connection errors. A single stuck call can therefore hold the request for up to 30 minutes in the very worst case.
- `evaluation_endpoint` is `async def` but calls blocking code: **the event loop is blocked for the whole generation**. While one student waits, every other request to the server waits too (chat streaming, pages, other evaluations).
- Mistral limits: **not readable from the public docs** (I fetched the models page: no rate limits there). They are per-workspace and shown in the Mistral console, *Limits* page (<https://console.mistral.ai/>), under the account's tier. **TODO (needs the account): read requests/second, tokens/minute and tokens/month there and write the value and the date here.** Do not use a number from memory.

### Assumption

One `ministral-14b-latest` call that returns one question (~400–600 output tokens of JSON) takes **about 4–6 s**, 5 s used below. 5 % of calls return invalid JSON and are retried once. To be measured with a stopwatch on the fork (time `POST /session/evaluation` with n=10) and corrected.

### The number

| Case | Calls | Wait |
|------|-------|------|
| Default n=10, no retry | 10 | **≈ 50 s** |
| n=10, 5 % retried | ≈ 11 | ≈ 55 s |
| Max n=20, no retry | 20 | ≈ 100 s |
| n=20, every question fails twice | 60 | ≈ 300 s |
| n=10, 429 from Mistral with SDK back-off | 10+ | adds seconds per hit; not bounded by the code |

**Answer: a student waits about 50 s for a default evaluation test, and about 100 s for the largest one, with a worst case of several minutes and no upper bound in the code.** That is above the 60 s assumed in question 1 as soon as n≥12, and while it lasts, other users are frozen.

Cost of concurrency: the event loop is blocked, so evaluations queue one behind the other. With 30 students clicking at once, the last waits about 30 × 50 s = **25 min**. The load on Mistral stays low (one call at a time, ≈ 0.2 req/s), so the request-rate limit is not the problem; tokens/minute and tokens/month remain to check.

### Seam I think holds it

The **question generator**: the single place where "a question for this competence" is asked of the LLM, today `call_mistral` + `generate_*_test` (`fonctions_python/base_generator.py` and `type_questions/`). Its callers (`generate_mixed_test`, then the endpoint) only need "give me these questions for these competences, within a deadline". Behind that seam we can add concurrency, a timeout, a cache/pre-generation, or a cheaper model without touching the endpoint. What its callers should see waits for Lab 2.

## 3. Open points before the Oral

- Measure the real latency per call (replaces the 5 s assumption).
- Read the Mistral limits and date them.
- Choose and defend the assumption on the wait (60 s? progress bar? pre-generation?).

## 4. Non-functional requirements, v1 (numbers and sources)

| NF requirement | Number | Source |
|----------------|--------|--------|
| Wait for an evaluation test (10 questions) | **≤ 60 s**, even if each LLM call takes 10 s (twice my 5 s estimate) | Assumption, from section 2: sequential code gives ≈ 50 s at 5 s/call and ≈ 100 s at 10 s/call; 60 s is what a student will sit through with a spinner. To confirm with the product owner (question 1) |
| Calls in flight to the LLM | **≤ 4 at once** | Assumption, below the free-tier request rate; to replace by the Mistral Limits page value (read on the day, not yet read) |
| Longest a single LLM call may hold a request | **30 s** (today: 600 s SDK default, `llm_client.py`) | Assumption: 3× the typical 10 s call |
| Attempts per question on invalid JSON | **3** | Existing `MAX_RETRIES` in `base_generator.py:35` |
| A failed question | never fails the whole test | Assumption: a test with 9 of 10 questions beats an error page |
| Concurrent students | 30 | Assumption, question 2 |

Seam: the `question_generation` package (see the Spec). 10 questions at 10 s/call, 4 at once: 3 rounds ≈ 30 s, inside the 60 s budget with room for one retry round.
