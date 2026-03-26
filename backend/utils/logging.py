import logging
import functools

def log_methods(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logging.info(f"→ {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logging.info(f"✓ {func.__name__}")
            return result
        except Exception as e:
            logging.error(f"✗ {func.__name__} | {e}")
            raise e
    return wrapper