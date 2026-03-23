import logging.config
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import create_async_engine

from athena.api import auth_router, images_router, sessions_router
from athena.models.base import Base
from athena.settings import get_settings


settings = get_settings()

logging.config.dictConfig(settings.LOGGING)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(lifespan=lifespan)

templates_dir = Path(__file__).parent / "athena/templates"
static_dir = Path(__file__).parent / "athena/static"
upload_dir = Path(settings.UPLOAD_DIR)

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

if upload_dir.exists():
    app.mount("/media", StaticFiles(directory=upload_dir), name="media")

app.include_router(auth_router)
app.include_router(images_router)
app.include_router(sessions_router)


@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = templates_dir / "index.html"
    if index_path.exists():
        return index_path.read_text()
    return "<h1>No template found</h1>"
