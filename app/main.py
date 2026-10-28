from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.db import schema
from app.models import AnalysisRequest, AnalysisResponse, SchemaResponse
from app.seed import seed
from app.workflow import analyze


ROOT = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_: FastAPI):
    from app.db import DB_PATH

    if not DB_PATH.exists():
        seed()
    yield


app = FastAPI(title="AI Business Analyst Agent", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/api/schema", response_model=SchemaResponse)
def get_schema() -> SchemaResponse:
    return SchemaResponse(tables=schema())


@app.post("/api/analyze", response_model=AnalysisResponse)
def post_analyze(request: AnalysisRequest) -> AnalysisResponse:
    try:
        return analyze(request.question)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
