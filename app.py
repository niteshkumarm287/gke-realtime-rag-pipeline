import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from log_writer import GCSLogWriter

app = FastAPI()

# ENV config (important for Docker/GKE)
BUCKET_NAME = os.getenv("BUCKET_NAME")

if not BUCKET_NAME:
    raise ValueError("BUCKET_NAME environment variable is required")


# Lazy init (prevents startup crash)
_writer = None


def get_writer():
    global _writer
    if _writer is None:
        _writer = GCSLogWriter(bucket_name=BUCKET_NAME)
    return _writer


class LogRequest(BaseModel):
    message: str
    level: str = "INFO"


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/log")
def write_log(req: LogRequest):
    try:
        log_entry = {
            "message": req.message,
            "level": req.level
        }

        writer = get_writer()
        blob_name = writer.write(log_entry)

        return {"written_to": blob_name}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))