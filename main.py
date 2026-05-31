import os
import uvicorn
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from telethon import TelegramClient
from telethon.errors import UsernameInvalidError, UsernameNotOccupiedError, FloodWaitError

# Настройка логирования, чтобы видеть ошибки в консоли Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ВАШИ ДАННЫЕ ---
API_ID = 20776429
API_HASH = '9c8955cc52c6df7e7c18def50d3838eb'

# Инициализация клиента. 
# Используем имя файла сессии, который вы загрузили в репозиторий
client = TelegramClient('checker_session', API_ID, API_HASH)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # При старте сервера
    logger.info("Запуск Telegram клиента...")
    await client.start()
    logger.info("✅ Клиент успешно запущен!")
    yield
    # При выключении
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
    return {"status": "Mini App Backend is live"}

if __name__ == "__main__":
    # Render автоматически задает PORT, используем его или 10000 по умолчанию
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
