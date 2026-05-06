import os
import logging
from contextlib import asynccontextmanager

from google import genai
from google.genai import types
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
PROJECT_ID  = os.environ["GCP_PROJECT"]
REGION      = os.environ.get("VERTEX_LOCATION", "us-central1")
CORPUS_NAME = os.environ["CORPUS_NAME"]
MODEL_NAME  = os.environ.get("MODEL_NAME", "gemini-2.5-flash")

# ── Global client ─────────────────────────────────────────────────────────────
_client: genai.Client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _client
    logger.info(f"Initialising google-genai | project={PROJECT_ID} location={REGION}")
    _client = genai.Client(vertexai=True, project=PROJECT_ID, location=REGION)
    logger.info(f"Model: {MODEL_NAME} | Corpus: {CORPUS_NAME}")
    yield

app = FastAPI(title="RAG Query API", lifespan=lifespan)

# ── Schemas ───────────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)

class QueryResponse(BaseModel):
    answer: str
    model: str

# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL_NAME}


@app.post("/query", response_model=QueryResponse)
async def query(req: QueryRequest):
    logger.info(f"Query: '{req.question[:80]}' top_k={req.top_k}")
    try:
        rag_tool = types.Tool(
            retrieval=types.Retrieval(
                vertex_rag_store=types.VertexRagStore(
                    rag_corpora=[CORPUS_NAME],
                    rag_retrieval_config=types.RagRetrievalConfig(
                        top_k=req.top_k,
                    ),
                )
            )
        )

        response = _client.models.generate_content(
            model=MODEL_NAME,
            contents=req.question,
            config=types.GenerateContentConfig(
                tools=[rag_tool],
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                temperature=1.0,
            ),
        )

        answer = response.text
        if not answer:
            raise ValueError("Model returned an empty response")

        logger.info("Query answered successfully")
        return QueryResponse(answer=answer, model=MODEL_NAME)

    except Exception as exc:
        logger.exception("Query failed")
        raise HTTPException(status_code=500, detail=str(exc))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)