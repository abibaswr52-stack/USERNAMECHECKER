import os
import uvicorn
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from telethon import TelegramClient
from telethon.errors import UsernameInvalidError, UsernameNotOccupiedError, FloodWaitError

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ВАШИ ДАННЫЕ ---
API_ID = 20776429
API_HASH = '9c8955cc52c6df7e7c18def50d3838eb'
BOT_TOKEN = '7253456538:AAHtQz0uC5ZoVFUkZ4653EzpZecoYGFq0Hg' # <--- ВСТАВЬТЕ ТОКЕН СЮДА

# Инициализация клиента
client = TelegramClient('bot_session', API_ID, API_HASH)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск через токен бота
    logger.info("Запуск Telegram бота через токен...")
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ Бот успешно запущен!")
    yield
    await client.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/check")
async def check_nick(nick: str):
    try:
        nick = nick.replace("@", "").strip()
        await client.get_entity(nick)
        return {"nick": nick, "free": False}
    except (ValueError, UsernameNotOccupiedError):
        return {"nick": nick, "free": True}
    except Exception as e:
        logger.error(f"Ошибка проверки {nick}: {e}")
        return {"nick": nick, "free": None, "error": str(e)}

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

if __name__ == "__main__":
    # Render использует переменную PORT
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
