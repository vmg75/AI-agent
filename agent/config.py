"""
Конфигурация приложения: переменные окружения, пути, лимиты.
"""

import contextvars
import os
from pathlib import Path

from dotenv import load_dotenv

# Загрузка .env при импорте модуля
load_dotenv()

# Базовый путь проекта (каталог agent/)
_BASE_DIR = Path(__file__).resolve().parent

# Пути
WORKSPACE_DIR = Path(os.getenv("AGENT_WORKSPACE", str(_BASE_DIR / "workspace")))
MEMORY_DIR = Path(os.getenv("AGENT_MEMORY_DIR", str(_BASE_DIR / "memory")))
CONVERSATION_FILE = MEMORY_DIR / "conversation.jsonl"
MEMORY_FILE = MEMORY_DIR / "memory.json"

# Модель OpenAI
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini-2025-08-07")

# API ключ
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# HTTP лимиты
HTTP_TIMEOUT = int(os.getenv("AGENT_HTTP_TIMEOUT", "30"))
HTTP_MAX_BYTES = int(os.getenv("AGENT_HTTP_MAX_BYTES", str(1024 * 1024)))  # 1MB
HTTP_MAX_REDIRECTS = int(os.getenv("AGENT_HTTP_MAX_REDIRECTS", "5"))

# Terminal лимиты
TERMINAL_TIMEOUT = int(os.getenv("AGENT_TERMINAL_TIMEOUT", "30"))
TERMINAL_MAX_OUTPUT_CHARS = int(os.getenv("AGENT_TERMINAL_MAX_OUTPUT_CHARS", "10000"))

# Параметры компакции памяти
MEMORY_MAX_MESSAGES = int(os.getenv("AGENT_MEMORY_MAX_MESSAGES", "100"))
MEMORY_MAX_SIZE_KB = int(os.getenv("AGENT_MEMORY_MAX_SIZE_KB", "1024"))
MEMORY_KEEP_RECENT = int(os.getenv("AGENT_MEMORY_KEEP_RECENT", "10"))

# Режим dry-run (устанавливается в run.py перед вызовом агента)
_dry_run_ctx: contextvars.ContextVar[bool] = contextvars.ContextVar("dry_run", default=False)
_verbose_ctx: contextvars.ContextVar[bool] = contextvars.ContextVar("verbose", default=False)


def get_dry_run() -> bool:
    """Проверить, активен ли режим dry-run."""
    return _dry_run_ctx.get()


def set_dry_run(value: bool) -> contextvars.Token:
    """Установить режим dry-run. Возвращает token для reset."""
    return _dry_run_ctx.set(value)


def reset_dry_run(token: contextvars.Token) -> None:
    """Сбросить dry-run к предыдущему значению."""
    _dry_run_ctx.reset(token)


def get_verbose() -> bool:
    """Проверить, активен ли режим verbose."""
    return _verbose_ctx.get()


def set_verbose(value: bool) -> contextvars.Token:
    """Установить режим verbose."""
    return _verbose_ctx.set(value)


def reset_verbose(token: contextvars.Token) -> None:
    """Сбросить verbose."""
    _verbose_ctx.reset(token)


def ensure_dirs() -> None:
    """Создать workspace и memory директории при первом запуске."""
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
