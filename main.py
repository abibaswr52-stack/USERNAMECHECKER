import os
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from telethon import TelegramClient, events

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ВАШИ ДАННЫЕ ---
API_ID = 20776429
API_HASH = '9c8955cc52c6df7e7c18def50d3838eb'
BOT_TOKEN = '7253456538:AAHtQz0uC5ZoVFUkZ4653EzpZecoYGFq0Hg' # <--- ВСТАВЬТЕ СЮДА ВАШ ТОКЕН

app = FastAPI()

# Разрешаем CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = TelegramClient('bot', API_ID, API_HASH)

# Приветствие без кнопок
@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    sender = await event.get_sender()
    name = sender.first_name if sender else "Друг"
    
    welcome_text = (
        f"**Привет, {name}!** 👋\n\n"
        "Добро пожаловать в **Nick Checker**.\n\n"
        "Я — ваш инструмент для поиска свободных юзернеймов в Telegram. "
        "Чтобы начать проверку, просто запустите **Mini App** через кнопку «Открыть» (Open) внизу экрана или в меню бота.\n\n"
        "🚀 *Система полностью готова к работе.*"
    )
    
    await event.respond(welcome_text)

# Запуск клиента
@app.on_event("startup")
async def startup_event():
    logger.info("Запуск Telegram бота...")
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ Бот успешно запущен!")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/check")
async def check_nick(nick: str):
    try:
        nick = nick.replace("@", "").strip()
        await client.get_entity(nick)
        return {"nick": nick, "free": False}
    except Exception:
        return {"nick": nick, "free": True}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
