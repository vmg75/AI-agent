"""
Тесты инструментов файловой системы: read_file, write_file, list_files.
"""

import json

import pytest

from agent.tools import list_files, read_file, write_file


def test_read_file_within_workspace(tmp_workspace):
    """Чтение файла внутри workspace."""
    (tmp_workspace / "test.txt").write_text("hello")
    out = read_file.invoke({"path": "test.txt"})
    assert out == "hello"


def test_read_file_outside_workspace(tmp_workspace):
    """Запрет чтения вне workspace."""
    out = read_file.invoke({"path": "../../etc/passwd"})
    assert "Ошибка" in out or "workspace" in out.lower()


def test_write_file_within_workspace(tmp_workspace):
    """Запись файла внутри workspace."""
    out = write_file.invoke({"path": "data/foo.txt", "content": "content"})
    assert "записано" in out.lower() or "Записано" in out
    assert (tmp_workspace / "data" / "foo.txt").read_text() == "content"


def test_write_file_outside_workspace(tmp_workspace):
    """Запрет записи вне workspace."""
    out = write_file.invoke({"path": "../../../tmp/hack.txt", "content": "x"})
    assert "Ошибка" in out or "workspace" in out.lower()


def test_list_files(tmp_workspace):
    """Список файлов."""
    (tmp_workspace / "a.txt").write_text("")
    (tmp_workspace / "subdir").mkdir()
    out = list_files.invoke({"path": "."})
    data = json.loads(out)
    names = [e["name"] for e in data]
    assert "a.txt" in names
    assert "subdir" in names
    assert any(e["type"] == "file" for e in data)
    assert any(e["type"] == "dir" for e in data)


def test_list_files_outside_workspace(tmp_workspace):
    """Запрет list вне workspace."""
    out = list_files.invoke({"path": "../../../"})
    assert "Ошибка" in out or "workspace" in out.lower()
