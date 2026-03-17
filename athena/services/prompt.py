import aiofiles

from athena.settings import get_settings


settings = get_settings()


async def get_prompt(name: str, **kwargs) -> str:
    async with aiofiles.open(settings.BASE_PATH / f"athena/prompts/{name}.md") as file:
        content = await file.read()
    if kwargs:
        return content.format(**kwargs)
    return content
