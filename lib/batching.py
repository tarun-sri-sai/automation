import time
from functools import wraps


def generate_batches(iterable, n):
    batch = []
    for item in iterable:
        batch.append(item)
        if len(batch) == n:
            yield batch
            batch = []
    if batch:
        yield batch


def incremental_retry(func):
    MAX_RETRIES = 3

    @wraps(func)
    def inner(*args, **kwargs):
        retries_left = MAX_RETRIES
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"{func.__name__} failed with {e}")
                if retries_left == 0:
                    raise Exception("Max retries exceeded with "
                                    f"{func.__name__}")

                print(f"{retries_left} retries left")
                time.sleep(20 * (2 ** (MAX_RETRIES - retries_left)))
                retries_left -= 1
    return inner
