import aiofiles

from athena.settings import get_settings


settings = get_settings()


async def get_prompt(name: str, **kwargs) -> str:
    if ".." in name or name.startswith("/"):
        raise ValueError(f"Invalid prompt name: {name}")

    prompt_path = settings.BASE_PATH / f"athena/prompts/{name}.md"
    try:
        async with aiofiles.open(settings.BASE_PATH / f"athena/prompts/{name}.md") as file:
            content = await file.read()
    except FileNotFoundError as e:
        raise ValueError(f"Prompt '{name}' not found at {prompt_path}") from e

    if kwargs:
        return content.format(**kwargs)
    return content
