"""
Инструменты агента: web search, HTTP, файлы, терминал, погода, крипта.
"""

import json
import subprocess
from typing import Any

import requests
try:
    from ddgs import DDGS
except ModuleNotFoundError:
    from duckduckgo_search import DDGS
from langchain_core.tools import tool

from agent.config import (
    HTTP_MAX_BYTES,
    HTTP_TIMEOUT,
    TERMINAL_MAX_OUTPUT_CHARS,
    TERMINAL_TIMEOUT,
    WORKSPACE_DIR,
    get_dry_run,
)
from agent.safety import is_allowed_command, is_safe_path, is_safe_url, validate_command_no_shell_injection


# --- Web Search ---


@tool
def web_search(query: str) -> str:
    """Поиск в интернете через DuckDuckGo. Возвращает список результатов: title, url, snippet.

    Args:
        query: Поисковый запрос
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
        output = []
        for r in results:
            output.append({
                "title": r.get("title", ""),
                "url": r.get("href", r.get("url", "")),
                "snippet": r.get("body", r.get("snippet", "")),
            })
        return json.dumps(output, ensure_ascii=False)
    except Exception as e:
        return f"Ошибка поиска: {e}"


# --- HTTP Request ---


@tool
def http_request(
    url: str,
    method: str = "GET",
    headers: dict | None = None,
    body: str | None = None,
) -> str:
    """Выполнить HTTP-запрос. Поддерживает GET и POST. Защита от SSRF (localhost, приватные сети запрещены).

    Args:
        url: URL для запроса
        method: HTTP метод (GET или POST)
        headers: Опциональные заголовки
        body: Тело запроса для POST
    """
    if not is_safe_url(url):
        return "Ошибка: URL запрещён (localhost, приватные сети)."
    method = method.upper()
    if method not in ("GET", "POST"):
        return f"Ошибка: поддерживаются только GET и POST, получено: {method}"
    try:
        resp = requests.request(
            method,
            url,
            headers=headers or {},
            data=body,
            timeout=HTTP_TIMEOUT,
            allow_redirects=True,
            stream=True,
        )
        content = b""
        for chunk in resp.iter_content(chunk_size=8192):
            content += chunk
            if len(content) > HTTP_MAX_BYTES:
                content = content[:HTTP_MAX_BYTES]
                break
        text = content.decode("utf-8", errors="replace")
        result = {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": text,
            "truncated": len(content) >= HTTP_MAX_BYTES,
        }
        return json.dumps(result, ensure_ascii=False)
    except requests.RequestException as e:
        return f"Ошибка HTTP: {e}"


# --- File IO ---


@tool
def read_file(path: str) -> str:
    """Прочитать содержимое файла в пределах workspace.

    Args:
        path: Путь к файлу (относительно workspace)
    """
    if not is_safe_path(path, WORKSPACE_DIR):
        return "Ошибка: путь вне workspace или содержит недопустимые элементы."
    full = (WORKSPACE_DIR / path).resolve()
    try:
        return full.read_text(encoding="utf-8")
    except FileNotFoundError:
        return f"Файл не найден: {path}"
    except OSError as e:
        return f"Ошибка чтения: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """Записать содержимое в файл в пределах workspace. Создаёт директории при необходимости.

    Args:
        path: Путь к файлу (относительно workspace)
        content: Содержимое для записи
    """
    if get_dry_run():
        return f"[DRY-RUN] Будет записано {len(content)} символов в {path}. Запустите без --dry-run для выполнения."
    if not is_safe_path(path, WORKSPACE_DIR):
        return "Ошибка: путь вне workspace или содержит недопустимые элементы."
    full = (WORKSPACE_DIR / path).resolve()
    try:
        full.parent.mkdir(parents=True, exist_ok=True)
        full.write_text(content, encoding="utf-8")
        return f"Записано {len(content)} символов в {path}"
    except OSError as e:
        return f"Ошибка записи: {e}"


@tool
def list_files(path: str = ".") -> str:
    """Список файлов и директорий в указанной папке workspace.

    Args:
        path: Путь к директории (по умолчанию корень workspace)
    """
    if not is_safe_path(path, WORKSPACE_DIR):
        return "Ошибка: путь вне workspace или содержит недопустимые элементы."
    full = (WORKSPACE_DIR / path).resolve()
    try:
        if not full.is_dir():
            return f"Не директория: {path}"
        entries = []
        for p in sorted(full.iterdir()):
            kind = "dir" if p.is_dir() else "file"
            entries.append({"name": p.name, "type": kind})
        return json.dumps(entries, ensure_ascii=False)
    except OSError as e:
        return f"Ошибка: {e}"


# --- Terminal Exec ---


@tool
def execute_terminal(command: str) -> str:
    """Выполнить команду в терминале. Разрешены: ls, cat, grep, head, tail, wc, python, pip, git status.
    Работает только в workspace. Shell отключён.

    Args:
        command: Команда с аргументами (например: ls -la, git status)
    """
    if get_dry_run():
        return f"[DRY-RUN] Будет выполнено: {command}. Запустите без --dry-run для выполнения."
    if not validate_command_no_shell_injection(command):
        return "Ошибка: команда содержит недопустимые символы (|, ;, &&, $ и т.д.)."
    if not is_allowed_command(command):
        return f"Ошибка: команда '{command.split()[0] if command.split() else ''}' не в allowlist. Разрешены: ls, cat, grep, head, tail, wc, python, pip, git status."
    args = command.split()
    if not args:
        return "Ошибка: пустая команда."
    try:
        result = subprocess.run(
            args,
            cwd=str(WORKSPACE_DIR),
            capture_output=True,
            text=True,
            timeout=TERMINAL_TIMEOUT,
            shell=False,
        )
        out = (result.stdout or "") + (result.stderr or "")
        if len(out) > TERMINAL_MAX_OUTPUT_CHARS:
            out = out[:TERMINAL_MAX_OUTPUT_CHARS] + "\n... (обрезано)"
        return f"exit_code={result.returncode}\n{out}"
    except subprocess.TimeoutExpired:
        return f"Ошибка: timeout ({TERMINAL_TIMEOUT}s)"
    except OSError as e:
        return f"Ошибка выполнения: {e}"


# --- Weather (Open-Meteo) ---


def _weather_code_description(code: int) -> str:
    """Перевод кода погоды Open-Meteo в текст."""
    codes = {
        0: "ясно", 1: "преимущественно ясно", 2: "переменная облачность",
        3: "пасмурно", 45: "туман", 48: "изморозь", 51: "морось",
        53: "морось", 55: "морось", 61: "дождь", 63: "дождь",
        65: "ливень", 71: "снег", 73: "снег", 75: "снег",
        77: "снежные зёрна", 80: "ливень", 81: "ливень", 82: "ливень",
        85: "снег", 86: "снег", 95: "гроза", 96: "гроза с градом",
    }
    return codes.get(code, "неизвестно")


@tool
def get_weather(city: str) -> str:
    """Получить текущую погоду в городе через Open-Meteo. При нескольких совпадениях выбирается самый населённый.

    Args:
        city: Название города (например: Berlin, Москва)
    """
    geocode_url = "https://geocoding-api.open-meteo.com/v1/search"
    try:
        gr = requests.get(
            geocode_url,
            params={"name": city, "count": 5, "language": "ru", "format": "json"},
            timeout=HTTP_TIMEOUT,
        )
        gr.raise_for_status()
        data = gr.json()
        results = data.get("results") or []
        if not results:
            return f"Город не найден: {city}"
        # Выбираем по population, иначе первый
        best = max(results, key=lambda r: r.get("population") or 0)
        lat = best["latitude"]
        lon = best["longitude"]
        name = best.get("name", city)
    except requests.RequestException as e:
        return f"Ошибка геокодинга: {e}"

    forecast_url = "https://api.open-meteo.com/v1/forecast"
    try:
        fr = requests.get(
            forecast_url,
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
            },
            timeout=HTTP_TIMEOUT,
        )
        fr.raise_for_status()
        curr = fr.json().get("current_weather", {})
    except requests.RequestException as e:
        return f"Ошибка прогноза: {e}"

    temp = curr.get("temperature", 0)
    wind = curr.get("windspeed", 0)
    code = curr.get("weathercode", 0)
    return json.dumps({
        "city": name,
        "temp_c": temp,
        "wind_kph": wind,
        "weather_code": code,
        "description": _weather_code_description(code),
    }, ensure_ascii=False)


# --- Crypto (CoinGecko) ---


@tool
def get_crypto_price(coin: str, currency: str = "usd") -> str:
    """Получить текущий курс криптовалюты. Поддерживаются id CoinGecko (bitcoin, ethereum и т.д.).

    Args:
        coin: ID монеты (bitcoin, ethereum, etc.)
        currency: Валюта (usd, eur, rub и т.д.)
    """
    url = "https://api.coingecko.com/api/v3/simple/price"
    try:
        r = requests.get(
            url,
            params={"ids": coin.lower(), "vs_currencies": currency.lower()},
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        data = r.json()
        if coin.lower() not in data:
            return f"Монета не найдена: {coin}. Проверьте id на coingecko.com"
        prices = data[coin.lower()]
        if currency.lower() not in prices:
            return f"Валюта не найдена: {currency}"
        price = prices[currency.lower()]
        return json.dumps({"coin": coin, "currency": currency, "price": price}, ensure_ascii=False)
    except requests.RequestException as e:
        return f"Ошибка API: {e}"


def get_all_tools() -> list:
    """Возвращает список всех инструментов для агента."""
    return [
        web_search,
        http_request,
        read_file,
        write_file,
        list_files,
        execute_terminal,
        get_weather,
        get_crypto_price,
    ]
