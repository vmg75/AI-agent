"""
Тесты безопасности HTTP URL (SSRF).
"""

import pytest

from agent.safety import is_safe_url


def test_safe_public_url():
    """Публичные URL разрешены."""
    assert is_safe_url("https://api.example.com/") is True
    assert is_safe_url("https://api.open-meteo.com/v1/forecast") is True


def test_forbidden_localhost():
    """localhost запрещён."""
    assert is_safe_url("http://localhost/") is False
    assert is_safe_url("http://localhost:8080/api") is False


def test_forbidden_127():
    """127.0.0.1 запрещён."""
    assert is_safe_url("http://127.0.0.1/") is False
    assert is_safe_url("http://127.0.0.1:3000/") is False


def test_forbidden_metadata():
    """169.254.169.254 (cloud metadata) запрещён."""
    assert is_safe_url("http://169.254.169.254/") is False


def test_forbidden_private_network():
    """Приватные сети запрещены."""
    assert is_safe_url("http://192.168.1.1/") is False
    assert is_safe_url("http://10.0.0.1/") is False
    assert is_safe_url("http://172.16.0.1/") is False
