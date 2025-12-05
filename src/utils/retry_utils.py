import time
import random
import functools
from typing import Type, Tuple, Union

def retry_with_backoff(
    retries: int = 3,
    backoff_in_seconds: float = 1.0,
    max_backoff_in_seconds: float = 10.0,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception
):
    """
    Exponential backoff retry decorator.
    
    Args:
        retries: Maximum number of retries.
        backoff_in_seconds: Initial backoff time in seconds.
        max_backoff_in_seconds: Maximum backoff time in seconds.
        exceptions: Exception types to catch and retry.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if x == retries:
                        print(f"❌ All {retries} retries failed for {func.__name__}: {e}")
                        raise
                    
                    sleep_time = min(
                        max_backoff_in_seconds,
                        backoff_in_seconds * (2 ** x) + random.uniform(0, 1)
                    )
                    print(f"⚠️ Error in {func.__name__}: {e}. Retrying in {sleep_time:.2f}s... ({x+1}/{retries})")
                    time.sleep(sleep_time)
                    x += 1
        return wrapper
    return decorator
