import logging.config
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from openrouter import OpenRouter
from pydantic import BaseModel

from settings import LOGGING, OPENROUTER_API_KEY


logging.config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

app = FastAPI()

templates_dir = Path(__file__).parent / "templates"
if templates_dir.exists():
    app.mount("/static", StaticFiles(directory=templates_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = templates_dir / "index.html"
    if index_path.exists():
        return index_path.read_text()
    return "<h1>No template found</h1>"


class PromptRequest(BaseModel):
    prompt: str


@app.post("/api/v1/image/")
def generate_image(request: PromptRequest) -> dict:
    with OpenRouter(api_key=OPENROUTER_API_KEY) as client:
        response = client.chat.send(
            model="google/gemini-3-pro-image-preview",
            messages=[{"role": "user", "content": request.prompt}],
            modalities=["image"],
        )

    images = response.choices[0].message.images
    return {"images": [x.image_url.url for x in images]}
