Draft. Rewrite by hand until you stand behind every line; keep the number, its source, what the module hides, what the test misses.

**Number:** 10 questions in at most 60 s when each LLM call takes 10 s. Source: my assumption in Design Document v1 section 4 (5 s/call measured: NOT YET, to measure; 10 s is the margin).

**What the module hides:** threads, the cap of 4 concurrent calls, the 30 s per-call timeout, retries on invalid JSON.

**What the test misses:** a real Mistral rate limit (429); the endpoint still blocks the event loop because it is not yet wired; abandoned hung threads are only reclaimed when the LLM answers; time is scaled by 1/10, so scheduler jitter is not representative.
