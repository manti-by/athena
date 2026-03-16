from fastapi import APIRouter
from openrouter import OpenRouter

from athena.schemas.api import PromptRequest
from athena.settings import get_settings


router = APIRouter(prefix="/api/v1", tags=["api"])
settings = get_settings()


@router.post("/image")
async def generate_image(request: PromptRequest) -> dict:
    content = [{"type": "text", "text": request.prompt}]
    if request.images:
        for img in request.images:
            content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img}"}})

    async with OpenRouter(api_key=settings.OPENROUTER_API_KEY) as client:
        response = await client.chat.send_async(
            model="google/gemini-3-pro-image-preview",
            messages=[{"role": "user", "content": content}],
            modalities=["image"],
        )

    print(response)

    images = response.choices[0].message.images or []
    return {"images": [x.image_url.url for x in images]}
