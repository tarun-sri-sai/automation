import hashlib
import json
import logging
from datetime import timedelta
from diskcache import Cache
from functools import wraps

CACHE_TTL = timedelta(days=7)
cache = Cache("temp")


def sqlite_cache(ttl=CACHE_TTL.total_seconds()):

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            key_data = {
                "func": func.__module__ + "." + func.__qualname__,
                "args": args,
                "kwargs": kwargs,
            }
            cache_key = hashlib.sha256(json.dumps(
                key_data, sort_keys=True, default=str
            ).encode()).hexdigest()

            sentinel = object()
            result = cache.get(cache_key, default=sentinel)
            if result is not sentinel:
                logging.debug(f"cache HIT for [{func.__name__}] with args "
                              f"[{args}] and kwargs {kwargs}")
                return result

            logging.debug(f"cache MISS for [{func.__name__}] with args "
                          f"[{args}] and kwargs [{kwargs}]")
            result = func(*args, **kwargs)
            cache.set(
                cache_key,
                result,
                expire=ttl
            )
            return result

        return wrapper

    return decorator
