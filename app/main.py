from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.routes import router as api_router
from app.config import APP_HOST, APP_PORT, APP_TITLE, BACKUP_DIR, DATABASE_PATH
from app.db import SessionLocal, init_db
from app.logging_config import configure_logging
from app.seed import bootstrap_demo_state


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    import logging

    logging.getLogger(__name__).info("Starting Renter Dashboard at database %s", DATABASE_PATH)
    init_db()
    with SessionLocal() as session:
        bootstrap_demo_state(session)
    yield


app = FastAPI(title=APP_TITLE, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.include_router(api_router)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "title": APP_TITLE,
        },
    )


@app.get("/BOOKMARKLET.md", response_class=PlainTextResponse)
def bookmarklet_documentation():
    return Path("BOOKMARKLET.md").read_text(encoding="utf-8")


def run() -> None:
    uvicorn.run("app.main:app", host=APP_HOST, port=APP_PORT, reload=True)


if __name__ == "__main__":
    run()
