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

Исходные файлы **не входят в репозиторий** (PDF, ~1 GB). Передавайте их на сервер через `rsync` или `scp`.

| Файл / папка | Формат | Назначение |
|---|---|---|
| `data/TN-ved_rus.pdf` | PDF 194 стр. | Классификатор: 17 015 кодов с иерархией |
| `data/Poyasneniya/*.pdf` | 2006 PDF-страниц | RAG-корпус: пояснительные примечания |
| `data/Rules_tn_ved/*.pdf` | 9 PDF | 6 Общих правил интерпретации |
| `data/ПК-181.md` | Markdown (узб. кириллица) | 1 833 ставки ввозных пошлин |

После ingestion в `data/build/` появляются готовые JSON-файлы и кеш эмбеддингов —  
повторный запуск пропускает уже выполненные шаги.

---

## Деплой на сервер

### Первый запуск (новый сервер)

```bash
# 1. Клонировать код
git clone https://github.com/komrxn/Tif_tn_ai.git
cd Tif_tn_ai

# 2. Скопировать исходные данные (с локальной машины)
rsync -av --progress \
  TN-ved_rus.pdf ПК-181.md Poyasneniya/ Rules_tn_ved/ \
  user@your-server:/path/to/Tif_tn_ai/data/

# 3. Создать .env (пример ниже)
cp .env.example .env && nano .env

# 4. Поднять БД и запустить ingestion (внутри Docker — нет проблем с зависимостями)
docker compose up -d surrealdb
docker compose --profile ingest run --rm ingestion

# 5. Запустить бот
docker compose up -d bot
```

Проверка:
```bash
curl http://localhost:8080/health
docker compose logs -f bot
```

### Обновление кода (повседневно)

```bash
git pull
docker compose build bot && docker compose up -d bot
```

Данные в SurrealDB сохраняются в именованном volume — пересоздавать не нужно.

### Переналить данные (если изменились источники)

```bash
docker compose up -d surrealdb
docker compose --profile ingest run --rm ingestion
docker compose restart bot
```

---

## Переменные окружения

Создайте `.env` в корне проекта:

```env
TELEGRAM_BOT_TOKEN=your_token
OPENAI_API_KEY=sk-...
ADMIN_TELEGRAM_ID=123456789

# значения по умолчанию — менять не нужно при Docker Compose
SURREAL_URL=ws://surrealdb:8000/rpc
SURREAL_USER=root
SURREAL_PASS=root
SURREAL_NS=tnved
SURREAL_DB=main
REDIS_URL=redis://redis:6379

LOG_LEVEL=INFO
```

---

## Структура проекта

```
.
├── src/
│   ├── main.py              # точка входа, сборка dispatcher
│   ├── config.py            # pydantic-settings (.env)
│   ├── session.py           # Redis: состояние диалога (TTL 30 мин)
│   ├── cards.py             # Redis: последние 10 карточек результатов
│   ├── health.py            # HTTP /health на порту 8080
│   ├── ai/
│   │   ├── llm.py           # classify(), list_examples()
│   │   ├── context.py       # Redis: история чата (3 хода, TTL 1 ч)
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
│       └── output_schema.json
├── ingestion/
│   ├── run_all.py           # оркестратор всего пайплайна
│   ├── parse_classifier.py  # TN-ved_rus.pdf → 17 015 кодов
│   ├── parse_duties.py      # ПК-181.md → 1 833 пошлины
│   ├── parse_explanations.py # Poyasneniya/*.pdf → 2 005 чанков
│   ├── embed.py             # эмбеддинги + SHA256-кеш на диске
│   └── load_surreal.py      # загрузка в SurrealDB пакетами по 500
├── tests/
├── Dockerfile
├── docker-compose.yml       # surrealdb + redis + bot + ingestion (profile)
└── pyproject.toml
```

---

## Разработка локально

```bash
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
