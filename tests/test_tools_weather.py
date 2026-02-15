"""
Тесты инструмента get_weather (Open-Meteo).
"""

import json

import pytest
import responses

from agent.tools import get_weather


@responses.activate
def test_get_weather_parses_response():
    """Корректный парсинг ответа погоды."""
    responses.add(
        responses.GET,
        "https://geocoding-api.open-meteo.com/v1/search",
        json={
            "results": [
                {"name": "Berlin", "latitude": 52.52, "longitude": 13.41, "population": 3644000},
            ]
        },
    )
    responses.add(
        responses.GET,
        "https://api.open-meteo.com/v1/forecast",
        json={
            "current_weather": {
                "temperature": 15.5,
                "windspeed": 12.0,
                "weathercode": 1,
            }
        },
    )
    out = get_weather.invoke({"city": "Berlin"})
    data = json.loads(out)
    assert data["city"] == "Berlin"
    assert data["temp_c"] == 15.5
    assert data["wind_kph"] == 12.0
    assert data["weather_code"] == 1
    assert "description" in data


@responses.activate
def test_get_weather_selects_most_populated():
    """При нескольких городах выбирается самый населённый."""
    responses.add(
        responses.GET,
        "https://geocoding-api.open-meteo.com/v1/search",
        json={
            "results": [
                {"name": "Berlin", "latitude": 52.52, "longitude": 13.41, "population": 100},
                {"name": "Berlin", "latitude": 50.0, "longitude": 10.0, "population": 5000000},
            ]
        },
    )
    responses.add(
        responses.GET,
        "https://api.open-meteo.com/v1/forecast",
        json={"current_weather": {"temperature": 10, "windspeed": 5, "weathercode": 0}},
    )
    out = get_weather.invoke({"city": "Berlin"})
    data = json.loads(out)
    assert data["city"] == "Berlin"
    # Должен быть выбран город с population 5000000
    assert "temp_c" in data


@responses.activate
def test_get_weather_city_not_found():
    """Город не найден."""
    responses.add(
        responses.GET,
        "https://geocoding-api.open-meteo.com/v1/search",
        json={"results": []},
    )
    out = get_weather.invoke({"city": "NonExistentCity123"})
    assert "не найден" in out.lower() or "not found" in out.lower()
