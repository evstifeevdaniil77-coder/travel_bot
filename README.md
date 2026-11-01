# travel_bot

Telegram-бот на `aiogram 3.x` для проведения CustDev-опроса путешественников.

## Установка и запуск

1. Клонируйте репозиторий и создайте файл `.env` на основе `.env.example`:
   ```bash
   cp .env.example .env
   ```
2. Укажите в `.env` ваш `BOT_TOKEN` и `ADMIN_CHAT_ID`.
3. Установите зависимости и запустите бота:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```
