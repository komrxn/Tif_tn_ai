# TN VED Assistant 🇺🇿

Telegram-бот для классификации товаров по кодам ТН ВЭД Республики Узбекистан (2022).  
Определяет 10-значный код, таможенную пошлину, показывает пояснения и иерархию классификатора.

---

## Возможности

- **Классификация текстом** — опишите товар, бот выдаст код с обоснованием и уровнем уверенности
- **Загрузка фото** — распознаёт товар по изображению через GPT-4 Vision
- **Голосовые сообщения** — транскрибирует через OpenAI Whisper (uz/ru/en)
- **Диалоговый режим** — до 5 уточняющих вопросов на обычном языке (не про коды ТН ВЭД)
- **Поправки** — бот понимает "нет, грузовой" как уточнение предыдущего результата
- **Таможенная пошлина** — ставки из ПК-181, включая min USD/кг, USD/шт, USD/л
- **Иерархия** — показывает цепочку от секции до 10-значного кода
- **Пояснения** — официальные пояснительные примечания (2005 страниц)
- **Примеры** — типичные товары для кода, генерируются LLM на основе примечаний
- **История** — последние 10 результатов с полными карточками (Redis, 30 дней)
- **Три языка** — 🇺🇿 O'zbek · 🇷🇺 Русский · 🇬🇧 English

---

## Стек

| Компонент | Технология |
|---|---|
| Бот | Python 3.11+, [aiogram](https://aiogram.dev/) 3.x |
| LLM | OpenAI `gpt-5.1` (structured output, JSON schema) |
| Эмбеддинги | `text-embedding-3-large` (1536 dim) |
| База данных | [SurrealDB](https://surrealdb.com/) 3.x — граф + вектор (HNSW, COSINE) |
| Сессии / история | Redis 7 |
| Контейнеры | Docker Compose |
| Линтер / форматер | [Ruff](https://docs.astral.sh/ruff/) |
| Тесты | pytest + pytest-asyncio |
| Зависимости | [uv](https://docs.astral.sh/uv/) |

---

## Архитектура

```
Telegram user
     │
     ▼
aiogram handlers (query / photo / voice / code_actions / history)
     │
     ├── RAG retriever ──► SurrealDB HNSW vector search
     │        │
     │        ▼
     │   build_context (classifier metadata + chunk text, ~3000 tokens)
     │
     ├── classify() ──► OpenAI gpt-5.1
     │        │         (system prompt + rules + context + history)
     │        ▼
     │   ClassifyResult (code, name, justification, confidence,
     │                   next_question, alternative_codes)
     │
     ├── Redis session  (clarifying dialogue state, TTL 30 min)
     ├── Redis history  (last 3 queries, TTL 1 h)
     └── Redis cards    (last 10 full result cards, TTL 30 days)
```

---

## Данные

| Источник | Формат | Назначение |
|---|---|---|
| `TN-ved_rus.pdf` | PDF 194 стр. | Классификатор: 17 015 кодов с иерархией |
| `Poyasneniya/*.pdf` | 2006 PDF-страниц | RAG-корпус: пояснительные примечания |
| `Rules_tn_ved/*.pdf` | 9 PDF | 6 Общих правил интерпретации |
| `ПК-181.md` | Markdown (узб. кириллица) | 1 833 ставки ввозных пошлин |

---

## Быстрый старт

### 1. Переменные окружения

Создайте `tnved-bot/.env`:

```env
TELEGRAM_BOT_TOKEN=your_token
OPENAI_API_KEY=sk-...
ADMIN_TELEGRAM_ID=123456789
SURREAL_URL=ws://surrealdb:8000/rpc
SURREAL_USER=root
SURREAL_PASS=root
SURREAL_NS=tnved
SURREAL_DB=main
REDIS_URL=redis://redis:6379
```

### 2. Подготовить данные

```bash
cd tnved-bot
uv run python -m ingestion.run_all
```

Это последовательно:
1. Парсит `TN-ved_rus.pdf` → 17 015 кодов
2. Парсит `ПК-181.md` → 1 833 пошлины
3. Загружает правила ОПИ
4. Парсит `Poyasneniya/*.pdf` → 2 005 чанков
5. Делает эмбеддинги через OpenAI (кеш на диске)
6. Загружает всё в SurrealDB

Повторный запуск идемпотентен — пропускает уже готовые шаги.

### 3. Запустить

```bash
docker compose up -d --build
```

Проверка:
```bash
curl http://localhost:8080/health
```

---

## Структура проекта

```
tnved-bot/
├── src/
│   ├── main.py              # точка входа, сборка dispatcher
│   ├── config.py            # pydantic-settings (.env)
│   ├── session.py           # Redis: состояние диалога
│   ├── cards.py             # Redis: последние 10 карточек результатов
│   ├── health.py            # HTTP /health на порту 8080
│   ├── ai/
│   │   ├── llm.py           # classify(), list_examples()
│   │   ├── context.py       # Redis: история чата (3 хода)
│   │   └── embeddings.py    # OpenAI embeddings
│   ├── db/
│   │   ├── client.py        # SurrealDB singleton
│   │   └── repo.py          # все запросы к БД
│   ├── handlers/
│   │   ├── query.py         # текстовые запросы + диалоговый цикл
│   │   ├── code_actions.py  # кнопки: пошлины, дерево, пояснения, примеры, назад
│   │   ├── history.py       # /history — последние результаты
│   │   ├── photo.py         # классификация по фото
│   │   └── voice.py         # транскрипция голоса
│   ├── middleware/
│   │   ├── user.py          # создание/загрузка пользователя
│   │   ├── ratelimit.py     # 40 запросов/день
│   │   └── logging.py       # логирование обновлений
│   ├── rag/
│   │   ├── retriever.py     # HNSW vector search
│   │   └── prompts.py       # сборка контекста для LLM
│   ├── ui/
│   │   ├── formatters.py    # форматирование карточек в HTML
│   │   ├── keyboards.py     # inline и reply клавиатуры
│   │   └── i18n.py          # локализация (uz/ru/en)
│   ├── locales/             # ru.json, uz.json, en.json
│   └── prompts/
│       ├── system_base.md   # системный промпт классификатора
│       └── output_schema.json # JSON schema для structured output
├── ingestion/
│   ├── run_all.py           # запуск всего пайплайна
│   ├── parse_classifier.py  # PDF → коды
│   ├── parse_duties.py      # MD → пошлины
│   ├── parse_explanations.py # PDF → чанки
│   ├── embed.py             # эмбеддинги + кеш
│   └── load_surreal.py      # загрузка в БД
├── tests/
│   ├── test_parse_classifier.py
│   ├── test_parse_duties.py
│   ├── test_retriever.py
│   └── golden_set.py
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

---

## Разработка

```bash
# установить зависимости
uv sync

# линтер + форматер
uv run ruff check . && uv run ruff format .

# тесты
uv run pytest
```

---

## Команды бота

| Команда | Описание |
|---|---|
| `/start` | Приветствие, выбор языка |
| `/language` | Сменить язык |
| `/history` | Последние 10 классификаций |
| `/help` | Справка |

---

## Лицензия

MIT
