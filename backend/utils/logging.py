import logging
import functools

def log_methods(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Entry Log
        logging.info(f"Entering: {func.__name__} | Args: {args}, Kwargs: {kwargs}")
        try:
            result = func(*args, **kwargs)
            # Exit Log (Success)
            logging.info(f"Exiting: {func.__name__} | Result: {result}")
            return result
        except Exception as e:
            # Exit Log (Exception)
            logging.error(f"Exiting: {func.__name__} | Exception: {e}")
            raise e
    return wrapper