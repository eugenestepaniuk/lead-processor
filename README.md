# Lead Processor

**Lead Processor** — MVP-бекенд для обробки заявок із лендингу. Пайплайн працює послідовно:
прийом → валідація → нормалізація → AI-summary + класифікація → запис у SQLite → сповіщення в Telegram.
Це MVP/прототип, **не production-ready**.

---

## Стек

- Python 3.11+
- FastAPI + Uvicorn
- Pydantic v2, pydantic-settings
- Google Gen AI SDK (`google-genai`, модель `gemini-2.5-flash`)
- SQLite (stdlib)
- httpx
- pytest, Ruff, mypy

---

## Встановлення

Створіть віртуальне середовище, активуйте його та встановіть залежності:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Налаштування .env

Скопіюйте `.env.example` у `.env` і заповніть значення. Конфіг читається через pydantic-settings.

```bash
cp .env.example .env
```

| Змінна | Призначення |
|---|---|
| `PORT` | порт сервера (за замовч. 8000) |
| `LOG_LEVEL` | рівень логів (`info`/`debug`/...) |
| `APP_ENV` | середовище (`development`) |
| `AI_ENABLED` | вмикає AI-крок (`true`/`false`) |
| `GEMINI_API_KEY` | ключ Google AI Studio (потрібен, якщо `AI_ENABLED=true`) |
| `AI_MODEL` | модель Gemini (`gemini-2.5-flash`) |
| `SQLITE_PATH` | шлях до файлу БД (`./data/leads.db`) |
| `TELEGRAM_ENABLED` | вмикає сповіщення (`true`/`false`) |
| `TELEGRAM_BOT_TOKEN` | токен бота (потрібен, якщо `TELEGRAM_ENABLED=true`) |
| `TELEGRAM_CHAT_ID` | ID чату для сповіщень (потрібен, якщо `TELEGRAM_ENABLED=true`) |

> **Запуск без зовнішніх сервісів:** поставте `AI_ENABLED=false` і `TELEGRAM_ENABLED=false` —
> пайплайн працює з фолбеками (summary = `None`, без сповіщення), заявка все одно валідовується й
> записується в SQLite.

---

## Отримання ключа Gemini

1. Відкрийте https://aistudio.google.com/app/apikey та увійдіть Google-акаунтом.
2. Натисніть **Create API key** (можна в новому проєкті або в наявному).
3. Скопіюйте ключ (починається з `AIzaSy…`) у `.env` → `GEMINI_API_KEY`.

> Ключі, створені зараз в AI Studio, за замовчуванням є «auth keys» і працюють одразу; не
> перевикористовуйте старі «unrestricted standard» ключі — створіть новий.

---

## Отримання токена та chat_id Telegram

1. У Telegram напишіть боту **@BotFather**, виконайте `/newbot`, дайте ім'я та username бота —
   отримаєте токен виду `123456789:AA...`. Вставте у `.env` → `TELEGRAM_BOT_TOKEN`.
2. Надішліть будь-яке повідомлення своєму новому боту (натисніть **Start**) — інакше бот не «бачить» чат.
3. Відкрийте у браузері (підставивши токен):
   `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. У відповіді знайдіть `"chat":{"id": ...}` — це значення `TELEGRAM_CHAT_ID`
   (для особистого чату — додатне число; для груп — від'ємне).

---

## Запуск

```bash
uvicorn app.main:app --reload --port 8000
```

Сервер підніметься на http://localhost:8000. Health-check: `GET /health` → `{"status":"ok"}`.

---

## Приклад запиту

Файл `examples/payload.json` містить готовий приклад заявки з усіма полями:

```bash
curl -X POST http://localhost:8000/api/leads \
  -H "Content-Type: application/json" \
  -d @examples/payload.json
```

У відповідь повертається JSON `ProcessResult` з полями `lead_id`, `summary`, `category`, `ai_ran`, `notified`.

> **Windows PowerShell:** використовуйте `curl.exe`, бо `curl` там — аліас `Invoke-WebRequest`.

---

## Як це працює

Ендпоінт `POST /api/leads` приймає JSON-заявку; FastAPI валідує її за Pydantic-моделлю `LeadIn`
(обов'язковий `name`; правило «має бути хоча б один контакт — email або phone»). Невалідний вхід → `422`.

Пайплайн (`app/pipeline/process_lead.py`) виконує кроки послідовно й синхронно:
`normalize → AI (summary + класифікація) → save (SQLite) → format → notify (Telegram)`.

Поділ помилок:
- **Критичні** (валідація → `422`; запис у БД → пробрасується, `5xx`) зупиняють обробку.
- **Некритичні** (AI, Telegram) ловляться всередині сервісів і дають фолбек, не валлячи пайплайн.

Семантика AI-результату: відсутній результат (`ai_ran=false`) означає, що AI вимкнено або стався
інфра-збій; `category="unknown"` — AI відповів, але вміст незрозумілий. AI повертає `summary` +
категорію (`hot`/`warm`/`cold`/`unknown`).

---

## Тести та якість

```bash
ruff check .
mypy app
pytest -q
```

