# Архитектура CLI AI-агента

## Обзор

Локальный терминальный агент, использующий **OpenAI** и **LangChain** для понимания запросов на естественном языке, выбора инструментов и формирования структурированных ответов. Работает без баз данных — все данные хранятся в файлах.

---

## Диаграмма потока данных

```
┌─────────────┐     ┌───────────────┐    ┌─────────────────┐
│   CLI       │────▶│  process_query│───▶│  create_agent   │
│  (run.py)   │     │  (agent.py)   │    │  (LangChain)    │
└─────────────┘     └──────┬────────┘    └────────┬────────┘
                           │                      │
                           │  load context        │  tool calls
                           ▼                      ▼
                    ┌──────────────┐     ┌─────────────────┐
                    │   memory/    │     │    tools.py     │
                    │ conversation │     │ (web, http, fs, │
                    │ memory.json  │     │  terminal, etc) │
                    └──────────────┘     └────────┬────────┘
                           ▲                      │
                           │  append + compact    │  safety checks
                           └──────────────────────┘
```

---

## Компоненты

### 1. CLI (run.py)

**Назначение:** точка входа, парсинг аргументов, режимы работы.

**Режимы:**
- **REPL** (по умолчанию) — интерактивный цикл ввода/вывода
- **--task "..."** — одноразовое выполнение запроса
- **--verbose** — логирование вызовов
- **--dry-run** — план без выполнения (write_file, execute_terminal)

**Подход:** argparse для простоты, без внешних CLI-фреймворков.

---

### 2. Агент (agent.py)

**Назначение:** сборка цепочки Router → Tool → Answer.

**Поток:**
1. Загрузка контекста из `memory` (summary + история)
2. Формирование сообщений для LLM (SystemMessage + HumanMessage)
3. Вызов `create_agent(llm, tools)` из `langchain.agents`
4. Подача запроса и получение результата
5. Извлечение финального AIMessage (без tool_calls)
6. Сохранение в память и компакция при необходимости

**Особенности:**
- Двухшаговая модель: LLM выбирает инструмент → Executor выполняет → LLM формирует ответ
- Контекст передаётся через `SystemMessage` (summary) + история диалога
- При нехватке контекста LLM предлагает уточняющий вопрос (через system prompt)

---

### 3. Инструменты (tools.py)

**Назначение:** типизированные функции с docstring для tool calling.

| Инструмент      | API/источник      | Ограничения                        |
|-----------------|-------------------|------------------------------------|
| web_search      | DuckDuckGo (ddgs) | max_results=5                      |
| http_request    | requests          | SSRF-проверка, timeout, max_bytes |
| read_file       | Path.read_text    | только workspace                   |
| write_file      | Path.write_text   | только workspace, dry-run         |
| list_files      | Path.iterdir      | только workspace                   |
| execute_terminal| subprocess.run    | allowlist, shell=False             |
| get_weather     | Open-Meteo        | геокодинг + выбор по population    |
| get_crypto_price| CoinGecko         | обработка ошибок                  |

**Подход:** декоратор `@tool` из LangChain — docstring и type hints задают схему для LLM.

---

### 4. Безопасность (safety.py)

**Принцип:** все внешние действия проходят валидацию.

| Проверка                   | Назначение                                          |
|----------------------------|-----------------------------------------------------|
| `is_safe_url()`            | SSRF: localhost, 127.x, 169.254.x, 10/8, 172.16/12, 192.168/16 |
| `is_safe_path()`           | Пути только в workspace, блокировка `..`           |
| `is_allowed_command()`     | allowlist: ls, cat, grep, head, tail, wc, python, pip, git status |
| `validate_command_no_shell_injection()` | Запрет \|, ;, &&, $, `, >, < |

**Подход:** hostname проверяется как IP только при наличии валидного IP; иначе трактуется как DNS-имя и допускается.

---

### 5. Память (memory.py)

**Назначение:** хранение истории без БД.

**Структура:**
- `conversation.jsonl` — построчный лог сообщений (role, content, ts)
- `memory.json` — сводка: summary, facts, todos, updated_at

**Компакция:**
При превышении лимитов (N сообщений или M KB):
1. Вызов LLM для генерации summary
2. Сохранение summary в memory.json
3. Удаление старых сообщений, оставление последних K реплик

**Параметры (config):** MEMORY_MAX_MESSAGES, MEMORY_MAX_SIZE_KB, MEMORY_KEEP_RECENT.

---

### 6. Конфигурация (config.py)

**Подход:** python-dotenv + переменные окружения.

- Пути: WORKSPACE_DIR, MEMORY_DIR
- LLM: OPENAI_MODEL, OPENAI_API_KEY
- Лимиты: HTTP_TIMEOUT, HTTP_MAX_BYTES, TERMINAL_TIMEOUT, TERMINAL_MAX_OUTPUT_CHARS
- Dry-run/verbose: contextvars для передачи в инструменты

---

### 7. LLM (llm_client.py)

**Назначение:** абстракция над OpenAI.

- `get_llm()` возвращает `ChatOpenAI` из langchain-openai
- Модель и ключ берутся из config

---

## Решения по реализации

### Без БД
Вся персистентность — через JSON/JSONL. Это упрощает развёртывание и отладку.

### Tool Calling
Строгий tool calling: инструменты имеют чёткие схемы через docstring и type hints, LLM вызывает их по имени с аргументами.

### Dry-run
Contextvars задают режим; write_file и execute_terminal в dry-run возвращают план и не выполняют действия.

### Fallback импортов
Поддержка и `ddgs`, и `duckduckgo_search` для совместимости с разными окружениями.

### Обработка ошибок
Инструменты возвращают понятные тексты на русском вместо исключений, чтобы агент мог их интерпретировать.

---

## Тестирование

- **Unit:** моки HTTP (responses), изолированный workspace/memory
- **Интеграция:** test_agent_returns_string с моком create_agent
- **Без сети:** Open-Meteo, CoinGecko замоканы в тестах

---

## Зависимости

- **LangChain** — create_agent, сообщения
- **langchain-openai** — ChatOpenAI
- **langchain-core** — @tool
- **requests** — HTTP
- **ddgs/duckduckgo-search** — поиск
- **python-dotenv** — конфигурация
- **pydantic** — типы (через LangChain)
