"""
Тесты инструмента get_crypto_price (CoinGecko).
"""

import json

import pytest
import responses

from agent.tools import get_crypto_price


@responses.activate
def test_get_crypto_price_parses_response():
    """Корректный парсинг ответа крипты."""
    responses.add(
        responses.GET,
        "https://api.coingecko.com/api/v3/simple/price",
        json={"bitcoin": {"usd": 50000.0}},
    )
    out = get_crypto_price.invoke({"coin": "bitcoin", "currency": "usd"})
    data = json.loads(out)
    assert data["coin"] == "bitcoin"
    assert data["currency"] == "usd"
    assert data["price"] == 50000.0


@responses.activate
def test_get_crypto_price_unknown_coin():
    """Неизвестная монета — понятное сообщение."""
    responses.add(
        responses.GET,
        "https://api.coingecko.com/api/v3/simple/price",
        json={},
    )
    out = get_crypto_price.invoke({"coin": "unknowncoin123", "currency": "usd"})
    assert "не найден" in out.lower() or "not found" in out.lower()


@responses.activate
def test_get_crypto_price_eur():
    """Валюта EUR."""
    responses.add(
        responses.GET,
        "https://api.coingecko.com/api/v3/simple/price",
        json={"ethereum": {"eur": 3000.0}},
    )
    out = get_crypto_price.invoke({"coin": "ethereum", "currency": "eur"})
    data = json.loads(out)
    assert data["currency"] == "eur"
    assert data["price"] == 3000.0
