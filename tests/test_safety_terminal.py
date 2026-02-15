"""
Тесты безопасности terminal exec.
"""

import pytest

from agent.safety import is_allowed_command, validate_command_no_shell_injection
from agent.tools import execute_terminal


def test_allowed_command_ls():
    """ls разрешён."""
    assert is_allowed_command("ls") is True
    assert is_allowed_command("ls -la") is True


def test_allowed_command_git_status():
    """git status разрешён."""
    assert is_allowed_command("git status") is True


def test_forbidden_command_rm(tmp_workspace):
    """rm не в allowlist."""
    assert is_allowed_command("rm -rf /") is False
    out = execute_terminal.invoke({"command": "rm -rf /"})
    assert "allowlist" in out or "не в" in out or "Ошибка" in out


def test_forbidden_shell_injection(tmp_workspace):
    """Запрет shell-инъекции."""
    assert validate_command_no_shell_injection("ls | cat") is False
    assert validate_command_no_shell_injection("ls; rm -rf /") is False
    assert validate_command_no_shell_injection("ls && rm -rf") is False
    out = execute_terminal.invoke({"command": "ls | cat"})
    assert "недопустимые" in out or "Ошибка" in out


def test_execute_terminal_allowed(tmp_workspace):
    """Выполнение разрешённой команды."""
    out = execute_terminal.invoke({"command": "ls"})
    assert "exit_code=" in out
