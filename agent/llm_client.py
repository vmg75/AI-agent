"""
Адаптер для OpenAI через LangChain.
"""

from langchain_openai import ChatOpenAI

from agent.config import OPENAI_API_KEY, OPENAI_MODEL


def get_llm(**kwargs) -> ChatOpenAI:
    """
    Возвращает экземпляр ChatOpenAI для использования в агенте.
    """
    return ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY or None,  # None -> из env OPENAI_API_KEY
        temperature=0,
        **kwargs,
    )
