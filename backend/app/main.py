from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .calculator import calculate
from .models import ClaimRequest, ClaimResponse
from .story import DISCLAIMER, generate_story

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(title="Генератор страховых историй")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    # Без кэша: после правок страницы браузер не показывает старую версию.
    return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})


@app.post("/api/claims/estimate", response_model=ClaimResponse)
def estimate(req: ClaimRequest) -> ClaimResponse:
    # Синхронный обработчик: FastAPI выполняет его в пуле потоков,
    # поэтому блокирующий вызов Claude не останавливает сервер.
    try:
        result = calculate(req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    story, source = generate_story(req, result)
    return ClaimResponse(
        compensation=result,
        story=story,
        story_source=source,
        disclaimer=DISCLAIMER,
    )
