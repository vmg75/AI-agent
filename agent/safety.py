"""
Политики безопасности: валидация URL, путей, команд.
"""

import ipaddress
from pathlib import Path
from urllib.parse import urlparse

from agent.config import WORKSPACE_DIR

# Команды, разрешённые для терминального выполнения (без аргументов в allowlist)
# git status — особая команда (два токена)
ALLOWED_COMMANDS = frozenset({
    "ls", "cat", "grep", "head", "tail", "wc",
    "python", "pip", "git",
})

# Для git разрешаем только статус
ALLOWED_GIT_SUBCOMMANDS = frozenset({"status"})


def is_safe_url(url: str) -> bool:
    """
    Проверка URL на SSRF: запрет localhost, 127.0.0.1,
    169.254.169.254 (metadata), приватных сетей (10/8, 172.16/12, 192.168/16).
    """
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname or parsed.netloc.split(":")[0].strip()
        if not hostname:
            return False

        # localhost и пустые
        lower = hostname.lower()
        if lower in ("localhost", "localhost.", ""):
            return False

        # 127.0.0.1
        if lower.startswith("127."):
            return False

        # метаданные облака
        if hostname == "169.254.169.254":
            return False
        if hostname.startswith("169.254."):
            return False

        # Проверка IP — только если hostname является IP-адресом
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private:
                return False
            if ip.is_loopback:
                return False
            if ip.is_link_local:
                return False
        except (ValueError, ipaddress.AddressValueError):
            # Не IP — hostname (example.com и т.д.), разрешаем
            pass
        return True
    except (ValueError, ipaddress.AddressValueError):
        return False


def is_safe_path(path: str, workspace_root: Path | None = None) -> bool:
    """
    Проверка пути: только внутри workspace, запрет .. и symlink-выхода.
    """
    root = workspace_root or WORKSPACE_DIR
    root = Path(root).resolve()
    try:
        resolved = (root / path).resolve()
        # должен быть внутри workspace
        return str(resolved).startswith(str(root))
    except (OSError, ValueError):
        return False


def is_allowed_command(cmd: str) -> bool:
    """
    Проверка команды против allowlist.
    Разрешены: ls, cat, grep, head, tail, wc, python, pip, git status.
    Запрещены: shell=True, pipe, redirect, произвольные команды.
    """
    parts = cmd.strip().split()
    if not parts:
        return False

    base = parts[0].lower()

    # базовые команды
    if base in ("ls", "cat", "grep", "head", "tail", "wc", "python", "pip"):
        return True

    if base == "git":
        if len(parts) < 2:
            return False
        sub = parts[1].lower()
        return sub in ALLOWED_GIT_SUBCOMMANDS

    return False


def validate_command_no_shell_injection(cmd: str) -> bool:
    """
    Дополнительная проверка на shell-инъекции:
    запрет |, ;, &&, ||, $, `, >, < и т.п.
    """
    forbidden = ("|", ";", "&&", "||", "$", "`", ">", "<", "\n", "\\")
    return not any(c in cmd for c in forbidden)
