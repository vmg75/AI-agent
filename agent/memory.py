"""
Работа с памятью: conversation.jsonl, memory.json, компакция.
"""

import json
from datetime import datetime

from agent.config import (
    CONVERSATION_FILE,
    MEMORY_FILE,
    MEMORY_KEEP_RECENT,
    MEMORY_MAX_MESSAGES,
    MEMORY_MAX_SIZE_KB,
    ensure_dirs,
)
from agent.llm_client import get_llm


def append_message(role: str, content: str) -> None:
    """Добавить сообщение в conversation.jsonl."""
    ensure_dirs()
    line = json.dumps({
        "role": role,
        "content": content,
        "ts": datetime.utcnow().isoformat() + "Z",
    }, ensure_ascii=False) + "\n"
    CONVERSATION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONVERSATION_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def load_conversation() -> list[dict]:
    """Загрузить историю диалога из conversation.jsonl."""
    if not CONVERSATION_FILE.exists():
        return []
    result = []
    with open(CONVERSATION_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return result


def load_memory() -> dict:
    """Загрузить memory.json."""
    if not MEMORY_FILE.exists():
        return {
            "summary": "",
            "facts": [],
            "todos": [],
            "updated_at": "",
        }
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"summary": "", "facts": [], "todos": [], "updated_at": ""}
    return {
        "summary": data.get("summary", ""),
        "facts": data.get("facts", []),
        "todos": data.get("todos", []),
        "updated_at": data.get("updated_at", ""),
    }


def update_memory(
    summary: str,
    facts: list[dict],
    todos: list[dict],
) -> None:
    """Обновить memory.json."""
    ensure_dirs()
    data = {
        "summary": summary,
        "facts": facts,
        "todos": todos,
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _should_compact() -> bool:
    """Проверить, нужна ли компакция."""
    if not CONVERSATION_FILE.exists():
        return False
    lines = 0
    size = 0
    with open(CONVERSATION_FILE, "rb") as f:
        for line in f:
            lines += 1
            size += len(line)
            if lines >= MEMORY_MAX_MESSAGES or size >= MEMORY_MAX_SIZE_KB * 1024:
                return True
    return False


def _generate_summary(messages: list[dict]) -> str:
    """Сгенерировать краткое резюме диалога через LLM."""
    if not messages:
        return ""
    text = "\n".join(
        f"{m.get('role', '?')}: {m.get('content', '')[:500]}"
        for m in messages
    )
    prompt = f"""Кратко резюмируй этот диалог (2-4 предложения на русском). Сохрани ключевые факты и решения.

{text}

Резюме:"""
    llm = get_llm()
    try:
        resp = llm.invoke(prompt)
        return (resp.content or "").strip()
    except Exception:
        return "Диалог сжат (резюме не сгенерировано)."


def compact_if_needed() -> None:
    """
    Если conversation.jsonl превышает лимиты — сгенерировать summary,
    очистить старые сообщения, оставить только summary + последние K реплик.
    """
    if not _should_compact():
        return
    messages = load_conversation()
    if len(messages) <= MEMORY_KEEP_RECENT:
        return

    to_summarize = messages[:-MEMORY_KEEP_RECENT]
    summary = _generate_summary(to_summarize)
    keep = messages[-MEMORY_KEEP_RECENT:]

    mem = load_memory()
    old_summary = mem.get("summary", "")
    combined = f"{old_summary}\n{summary}".strip() if old_summary else summary

    update_memory(
        summary=combined,
        facts=mem.get("facts", []),
        todos=mem.get("todos", []),
    )

    with open(CONVERSATION_FILE, "w", encoding="utf-8") as f:
        for m in keep:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
