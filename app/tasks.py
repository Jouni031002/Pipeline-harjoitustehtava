import time
import requests
from celery.exceptions import Reject
from celery.utils.log import get_task_logger
from .worker import celery
from .database import SessionLocal
from .models import URLResult

logger = get_task_logger(__name__)

@celery.task(bind=True, acks_late=True)
def fetch_url(self, url: str):
    db = SessionLocal()
    start = time.time()
    status = None
    error_message = None
    should_dead_letter = False

    try:
        r = requests.get(url, timeout=5)
        status = r.status_code
        logger.info(f"Fetched {url} with status {status}")
    except requests.RequestException as exc:
        error_message = str(exc)
        should_dead_letter = True
        logger.warning(f"URL failed: {url}. Sending task to dead-letter queue. Error: {exc}")
    except Exception as exc:
        error_message = str(exc)
        should_dead_letter = True
        logger.error(f"Unexpected error for URL: {url}: {exc}")

    duration = int((time.time() - start) * 1000)

    try:
        result = URLResult(
            url=url,
            status_code=status,
            response_ms=duration,
            error_message=error_message,
        )
        db.add(result)
        db.commit()
    finally:
        db.close()

    if should_dead_letter:
        raise Reject(error_message or "URL processing failed", requeue=False)