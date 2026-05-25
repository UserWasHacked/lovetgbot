# Love Telegram Bot

Telegram-бот на **aiogram 3** для персонализированных любовных текстов через **Google Gemini** (`google-generativeai`). Баланс генераций хранится в **SQLite**, оплата — **Telegram Stars** (XTR).

## Возможности

- Регистрация с **2 бесплатными** генерациями
- Пошаговый сценарий (FSM): адресат → повод → детали → длина
- Списание 1 генерации перед запросом к Gemini
- Покупка пакетов: 5 или 20 генераций за звёзды
- История генераций в БД

## Установка

```bash
cd C:\Users\nikan\Projects\love-telegram-bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Заполните `.env`:

- `BOT_TOKEN` — токен от [@BotFather](https://t.me/BotFather)
- `GEMINI_API_KEY` — ключ [Google AI Studio](https://aistudio.google.com/apikey)
- `GEMINI_MODEL` — по умолчанию `gemini-1.5-flash`

### Telegram Stars

В [@BotFather](https://t.me/BotFather) включите платежи для бота. Для цифровых товаров используется валюта **XTR**; `provider_token` оставляется пустым.

Цены настраиваются в `.env`: `PACK_5_STARS`, `PACK_20_STARS`.

## Запуск

```bash
python run.py
```

или

```bash
python -m bot.main
```

## Структура проекта

```
love-telegram-bot/
├── bot/
│   ├── config.py          # настройки из .env
│   ├── states.py          # FSM
│   ├── database.py        # aiosqlite
│   ├── keyboards.py
│   ├── prompts.py         # системный промпт Gemini
│   ├── middlewares.py
│   ├── main.py
│   ├── handlers/
│   │   ├── start.py
│   │   ├── menu.py
│   │   ├── create.py
│   │   └── payments.py
│   └── services/
│       └── gemini_service.py
├── run.py
├── requirements.txt
└── .env.example
```

## Расширение под ЮKassa

Модуль `payments.py` можно дополнить вторым провайдером: отдельные callback-кнопки, `provider_token` ЮKassa и валюта `RUB`. Логика зачисления генераций уже в `Database.add_generations` и `record_payment`.
