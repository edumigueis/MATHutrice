"""Generate many questions from an LLM within a time budget.

Hides threading, retries on invalid output and per-call timeouts. Callers pass
prompts and get questions back, in the same order.
"""

from ._internal._generate import generate_questions

__all__ = ["generate_questions"]
