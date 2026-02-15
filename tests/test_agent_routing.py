"""
Интеграционные тесты роутинга: запрос -> правильный инструмент.
"""

import pytest
import responses
from unittest.mock import patch, MagicMock

from agent.agent import process_query


@responses.activate
@pytest.mark.skip(reason="Требует OpenAI API key; запускать вручную с ключом")
def test_weather_routing():
    """Какая погода в Берлине? -> weather tool."""
    responses.add(
        responses.GET,
        "https://geocoding-api.open-meteo.com/v1/search",
        json={"results": [{"name": "Berlin", "latitude": 52.52, "longitude": 13.41, "population": 1}]},
    )
    responses.add(
        responses.GET,
        "https://api.open-meteo.com/v1/forecast",
        json={"current_weather": {"temperature": 10, "windspeed": 5, "weathercode": 0}},
    )
    # Без мока LLM нужен реальный ключ; для CI проверяем только вызов
    answer = process_query("Какая погода в Берлине?")
    assert "Berlin" in answer or "погод" in answer.lower() or "temp" in answer.lower()


@responses.activate
@pytest.mark.skip(reason="Требует OpenAI API key; запускать вручную с ключом")
def test_crypto_routing():
    """Сколько стоит bitcoin в eur? -> crypto tool."""
    responses.add(
        responses.GET,
        "https://api.coingecko.com/api/v3/simple/price",
        json={"bitcoin": {"eur": 45000}},
    )
    answer = process_query("Сколько стоит bitcoin в eur?")
    assert "bitcoin" in answer.lower() or "eur" in answer.lower() or "45000" in answer


def test_agent_returns_string(tmp_memory, mocker):
    """process_query возвращает строку (с моком LLM)."""
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "Ответ агента"
    mock_response.tool_calls = []
    mock_llm.invoke.return_value = mock_response

    def mock_create_react_agent(model, tools):
        def invoke(inputs):
            return {"messages": [mock_response]}
        agent = MagicMock()
        agent.invoke = invoke
        return agent

    mocker.patch("agent.agent.get_llm", return_value=mock_llm)
    mocker.patch("agent.agent.create_react_agent", side_effect=mock_create_react_agent)

    answer = process_query("Привет")
    assert answer == "Ответ агента"
