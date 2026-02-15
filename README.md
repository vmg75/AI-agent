# CLI AI Agent

Локальный терминальный AI-агент на Python с использованием OpenAI и LangChain. Понимает запросы на естественном языке, выбирает подходящий инструмент, выполняет действие и отвечает структурированно.

## Возможности

- **Web Search** — поиск через DuckDuckGo
- **HTTP API** — запросы к внешним API (с защитой от SSRF)
- **File IO** — чтение/запись файлов в пределах workspace
- **Terminal** — выполнение разрешённых команд
- **Weather** — погода через Open-Meteo API
- **Crypto** — курсы криптовалют через CoinGecko
- **Память** — история диалога и резюме в файлах (без БД)

## Требования

- Python 3.10+
- OpenAI API key

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

```bash
cp .env.example .env
# Отредактируйте .env и укажите OPENAI_API_KEY
```

## Запуск

**REPL режим (по умолчанию):**
```bash
python -m agent.run
```

**Одна команда:**
```bash
python -m agent.run --task "Какая погода в Берлине?"
```

**С флагами:**
```bash
python -m agent.run --verbose              # Показывать вызовы инструментов
python -m agent.run --dry-run --task "..." # План без выполнения (запрос подтверждения для записи/terminal)
```

## Запуск тестов

```bash
pytest
# или
python -m pytest
```

## Примеры запросов

- «Какая погода в Москве?»
- «Сколько стоит bitcoin в eur?»
- «Найди в интернете последние новости о Python»
- «Выведи список файлов в текущей папке»
- «Запиши в файл note.txt текст: напомнить о встрече»

## Архитектура

Подробное описание архитектуры, компонентов и подхода к реализации см. в [ARCHITECTURE.md](ARCHITECTURE.md).

## Структура проекта

```
agent/
  ├── agent.py      # Сборка агента
  ├── tools.py      # Инструменты
  ├── memory.py     # Память (файлы)
  ├── safety.py     # Политики безопасности
  ├── config.py     # Конфигурация
  ├── llm_client.py # Адаптер OpenAI
  ├── run.py        # CLI
  ├── workspace/    # Рабочая папка
  └── memory/       # conversation.jsonl, memory.json
```
