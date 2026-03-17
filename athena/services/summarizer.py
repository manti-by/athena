from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from athena.services.prompt import get_prompt
from athena.settings import get_settings


async def summarize_session(input_text: str) -> str:
    settings = get_settings()
    if not settings.GROQ_API_KEY or not settings.GROQ_MODEL:
        return input_text

    try:
        llm = ChatGroq(model=settings.GROQ_MODEL, temperature=0.1, max_tokens=2048, max_retries=2)
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", await get_prompt(name="summary")),
                ("human", "Text: {input_text}"),
            ]
        )
        chain = prompt | llm
        response = await chain.ainvoke({"input_text": input_text})
        return str(response.content)
    except (ValueError, ConnectionError, TimeoutError):
        return input_text
