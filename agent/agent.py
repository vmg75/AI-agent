"""
Сборка агента: router -> tool -> answer.
"""

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agent.config import reset_dry_run, reset_verbose, set_dry_run, set_verbose
from agent.llm_client import get_llm
from agent.memory import append_message, compact_if_needed, load_conversation, load_memory
from agent.tools import get_all_tools


SYSTEM_PROMPT = """Ты — helpful CLI-агент. Отвечай на русском, структурированно (итог + детали/источники).
Если контекста недостаточно — задай 1 уточняющий вопрос вместо угадывания.
Доступные инструменты: web_search, http_request, read_file, write_file, list_files, execute_terminal, get_weather, get_crypto_price."""


def _conversation_to_messages(conv: list[dict], memory_summary: str) -> list:
    """Преобразовать историю + summary в сообщения для LLM."""
    msgs = []
    if memory_summary:
        msgs.append(SystemMessage(content=f"Контекст из памяти:\n{memory_summary}"))
    msgs.append(SystemMessage(content=SYSTEM_PROMPT))
    for m in conv:
        role = m.get("role", "")
        content = m.get("content", "") or ""
        if role == "user" or role == "human":
            msgs.append(HumanMessage(content=content))
        elif role == "assistant" or role == "ai":
            msgs.append(AIMessage(content=content))
    return msgs


def process_query(query: str, *, verbose: bool = False, dry_run: bool = False) -> str:
    """
    Обработать запрос пользователя: загрузить контекст, вызвать агента, сохранить в память.

    Args:
        query: Текст запроса
        verbose: Показывать вызовы инструментов
        dry_run: Режим планирования без выполнения (для write_file, execute_terminal)
    """
    dry_token = set_dry_run(dry_run)
    verb_token = set_verbose(verbose)
    try:
        mem = load_memory()
        conv = load_conversation()
        tools = get_all_tools()
        llm = get_llm()
        agent = create_agent(llm, tools)

        msgs = _conversation_to_messages(conv, mem.get("summary", ""))
        msgs.append(HumanMessage(content=query))

        if verbose:
            print("[agent] Запуск агента...")

        result = agent.invoke({"messages": msgs})
        out_messages = result.get("messages", [])

        # Берём последний ответ ассистента (AIMessage с content, без tool_calls)
        answer = ""
        for m in reversed(out_messages):
            if isinstance(m, AIMessage) and m.content:
                tool_calls = getattr(m, "tool_calls", None) or []
                if not tool_calls:
                    answer = m.content
                    break

        if not answer:
            answer = "Ответ не получен."

        append_message("user", query)
        append_message("assistant", answer)
        compact_if_needed()

        return answer
    finally:
        reset_dry_run(dry_token)
        reset_verbose(verb_token)
