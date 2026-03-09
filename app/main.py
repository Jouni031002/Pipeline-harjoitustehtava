import time
from urllib.parse import urlparse
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlalchemy import desc, text
from sqlalchemy.exc import SQLAlchemyError

from .database import SessionLocal, engine
from .models import Base, URLResult
from .schemas import URLRequest
from .tasks import fetch_url

@asynccontextmanager
async def lifespan(app: FastAPI):
    max_attempts = 20
    delay_seconds = 2

    for attempt in range(1, max_attempts + 1):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE url_results ADD COLUMN IF NOT EXISTS error_message TEXT")
                )
            break
        except SQLAlchemyError:
            if attempt == max_attempts:
                raise
            time.sleep(delay_seconds)

    yield


app = FastAPI(lifespan=lifespan)

@app.post("/analyze")
def analyze_urls(payload: URLRequest):
    if len(payload.urls) > 10:
        raise HTTPException(status_code=400, detail="Max 10 URLs")

    invalid_urls = []
    for url in payload.urls:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            invalid_urls.append(url)

    if invalid_urls:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "All URLs must start with http:// or https://",
                "invalid_urls": invalid_urls,
            },
        )

    for url in payload.urls:
        fetch_url.delay(url)
    return {"queued": len(payload.urls)}

@app.get("/results")
def results():
    db = SessionLocal()
    rows = db.query(URLResult).order_by(desc(URLResult.processed_at), desc(URLResult.id)).all()
    data = [
        {
            "id": r.id,
            "url": r.url,
            "status_code": r.status_code,
            "response_ms": r.response_ms,
            "error_message": r.error_message,
            "processed_at": r.processed_at
        }
        for r in rows
    ]
    db.close()
    return data