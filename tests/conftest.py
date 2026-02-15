"""
Фикстуры для тестов.
"""

import json
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def tmp_workspace(monkeypatch):
    """Временный workspace для тестов."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        monkeypatch.setattr("agent.config.WORKSPACE_DIR", root)
        monkeypatch.setattr("agent.safety.WORKSPACE_DIR", root)
        monkeypatch.setattr("agent.tools.WORKSPACE_DIR", root)
        yield root


@pytest.fixture
def tmp_memory(monkeypatch):
    """Временная директория memory для тестов."""
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        monkeypatch.setattr("agent.config.MEMORY_DIR", root)
        monkeypatch.setattr("agent.config.CONVERSATION_FILE", root / "conversation.jsonl")
        monkeypatch.setattr("agent.config.MEMORY_FILE", root / "memory.json")
        monkeypatch.setattr("agent.memory.CONVERSATION_FILE", root / "conversation.jsonl")
        monkeypatch.setattr("agent.memory.MEMORY_FILE", root / "memory.json")
        yield root


@pytest.fixture
def sample_conversation(tmp_memory):
    """Заполнить conversation.jsonl тестовыми сообщениями."""
    conv_file = tmp_memory / "conversation.jsonl"
    lines = [
        {"role": "user", "content": "Привет", "ts": "2025-01-01T12:00:00Z"},
        {"role": "assistant", "content": "Здравствуйте!", "ts": "2025-01-01T12:00:01Z"},
    ]
    conv_file.write_text("\n".join(json.dumps(m, ensure_ascii=False) for m in lines))
    return conv_file
