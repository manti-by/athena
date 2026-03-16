import os
from typing import Any


try:
    from langchain_core.messages import HumanMessage
    from langchain_groq import ChatGroq

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False


class SummarizerService:
    def __init__(self) -> None:
        self.groq_api_key = os.environ.get("GROQ_API_KEY")
        self.model = os.environ.get("SUMMARIZER_MODEL", "llama-3.1-8b-instant")

    async def summarize_session(self, session_items: list[dict[str, Any]], images: list[str]) -> str:
        if not session_items:
            return ""

        item_texts = [f"User request {i + 1}: {item['text']}" for i, item in enumerate(session_items)]
        context = "\n".join(item_texts)

        if not LANGCHAIN_AVAILABLE or not self.groq_api_key:
            return context

        prompt = f"""Based on the following conversation history, provide a brief summary that captures the key context and user intent for continuing the image generation task:

{context}

Provide a concise 1-2 sentence summary that captures the essential context."""

        try:
            chat = ChatGroq(groq_api_key=self.groq_api_key, model=self.model)
            messages = [HumanMessage(content=prompt)]
            response = chat.invoke(messages)
            return response.content
        except (ValueError, ConnectionError, TimeoutError):
            return context
