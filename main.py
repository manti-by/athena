import os

import openai
from fastapi import FastAPI
from pydantic import BaseModel


OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

app = FastAPI()


class PromptRequest(BaseModel):
    prompt: str


@app.post("/api/v1/image/")
def generate_image(request: PromptRequest) -> dict:
    client = openai.OpenAI(
        base_url="https://openrouter.ai",
        api_key=OPENROUTER_API_KEY,
    )

    response = client.chat.completions.create(
        model="google/gemini-3-pro-image-preview",
        messages=[{"role": "user", "content": request.prompt}],
        extra_body={"modalities": ["image"]},
    )

    image_data_base64 = response.choices[0].message.content
    if not image_data_base64:
        raise ValueError("No image data in response")

    return {"image": image_data_base64}
