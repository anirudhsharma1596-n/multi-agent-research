
import time
import functools
import logging

logger = logging.getLogger(__name__)

def with_retry(max_retries: int = 3, backoff: float = 2.0, exceptions=(Exception,)):
    """
    Decorator that retries a function with exponential backoff.

    Usage:
        @with_retry(max_retries=3, backoff=2.0)
        def call_llm():
            ...

    Waits: 2s → 4s → 8s between retries.
    """
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_retries + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"[Retry] {fn.__name__} failed after {max_retries} attempts: {e}")
                        raise
                    wait = backoff ** attempt
                    logger.warning(f"[Retry] {fn.__name__} attempt {attempt} failed: {e}. Retrying in {wait}s...")
                    time.sleep(wait)
        return wrapper
    return decorator