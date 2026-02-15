"""
Тесты памяти: append, load, compact.
"""

import json

import pytest
from pytest_mock import MockerFixture

from agent import memory
from agent.memory import append_message, compact_if_needed, load_conversation, load_memory, update_memory


def test_append_and_load_conversation(tmp_memory):
    """Запись и чтение conversation.jsonl."""
    append_message("user", "Привет")
    append_message("assistant", "Здравствуйте!")
    conv = load_conversation()
    assert len(conv) == 2
    assert conv[0]["role"] == "user"
    assert conv[0]["content"] == "Привет"
    assert conv[1]["role"] == "assistant"
    assert conv[1]["content"] == "Здравствуйте!"


def test_load_memory_empty(tmp_memory):
    """Пустой memory.json."""
    m = load_memory()
    assert "summary" in m
    assert "facts" in m
    assert "todos" in m


def test_update_memory(tmp_memory):
    """Обновление memory.json."""
    update_memory(
        summary="Резюме",
        facts=[{"key": "k1", "value": "v1"}],
        todos=[{"text": "todo1", "status": "open"}],
    )
    m = load_memory()
    assert m["summary"] == "Резюме"
    assert len(m["facts"]) == 1
    assert m["facts"][0]["key"] == "k1"
    assert len(m["todos"]) == 1
    assert m["todos"][0]["text"] == "todo1"


def test_compact_reduces_messages(tmp_memory, mocker: MockerFixture):
    """Компакция уменьшает количество сообщений."""
    # Патчим LLM чтобы не ходить в API
    mocker.patch.object(memory, "get_llm")
    mock_llm = mocker.MagicMock()
    mock_llm.invoke.return_value = mocker.MagicMock(content="Краткое резюме диалога.")
    memory.get_llm.return_value = mock_llm

    # Создаём много сообщений
    conv_file = tmp_memory / "conversation.jsonl"
    for i in range(25):
        append_message("user" if i % 2 == 0 else "assistant", f"msg {i}")

    # Устанавливаем маленькие лимиты для компакции (патчим в модуле memory)
    mocker.patch.object(memory, "MEMORY_MAX_MESSAGES", 20)
    mocker.patch.object(memory, "MEMORY_KEEP_RECENT", 4)

    compact_if_needed()

    conv = load_conversation()
    assert len(conv) <= 4
    m = load_memory()
    assert m["summary"] == "Краткое резюме диалога."
