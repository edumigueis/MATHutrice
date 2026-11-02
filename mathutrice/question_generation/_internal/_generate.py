import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

logger = logging.getLogger(__name__)


def _call_with_timeout(llm: Callable[[str], str], prompt: str, timeout: float) -> str:
    """Run one LLM call; raise TimeoutError if it does not return in time.

    The call runs in a daemon thread. A hung call cannot be killed, but it no
    longer holds the caller: it is abandoned and ends whenever the LLM does.
    """
    result: dict = {}

    def run() -> None:
        try:
            result["value"] = llm(prompt)
        except BaseException as exc:  # handed back to the caller's thread
            result["error"] = exc

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    thread.join(timeout)
    if thread.is_alive():
        raise TimeoutError(f"LLM call exceeded {timeout} s")
    if "error" in result:
        raise result["error"]
    return result["value"]


def generate_questions(
    prompts: list[str],
    llm: Callable[[str], str],
    parse: Callable[[str], dict],
    *,
    max_concurrency: int = 4,
    call_timeout: float = 30.0,
    max_attempts: int = 3,
) -> list[dict | None]:
    """One question per prompt, in order; None where a prompt could not be answered.

    At most `max_concurrency` calls run at once. A call that raises ValueError
    in `parse` (invalid output) is retried up to `max_attempts` times. A call
    that times out or raises any other error gives None for that prompt.
    Never raises because of one prompt.
    """

    def one(prompt: str) -> dict | None:
        for attempt in range(1, max_attempts + 1):
            try:
                return parse(_call_with_timeout(llm, prompt, call_timeout))
            except ValueError as exc:
                logger.warning("attempt %d/%d invalid: %s", attempt, max_attempts, exc)
            except Exception as exc:
                logger.error("question abandoned: %r", exc)
                return None
        return None

    with ThreadPoolExecutor(max_workers=max_concurrency) as pool:
        return list(pool.map(one, prompts))
