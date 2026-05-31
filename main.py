import os
import asyncio
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from telethon import TelegramClient
from telethon.errors import UsernameInvalidError, UsernameNotOccupiedError, FloodWaitError

# --- НАСТРОЙКИ ---
API_ID = 20776429
API_HASH = '9c8955cc52c6df7e7c18def50d3838eb'

# Инициализация
client = TelegramClient('checker_session', API_ID, API_HASH)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Запуск клиента при старте сервера
    await client.start()
    print("✅ Telethon клиент запущен")
    yield
    # Отключение при остановке
    await client.disconnect()

app = FastAPI(lifespan=lifespan)

@app.get("/check")
async def check_nick(nick: str):
    try:
        nick = nick.replace("@", "")
        await client.get_entity(nick)
        return {"nick": nick, "free": False}
    except (ValueError, UsernameNotOccupiedError):
        return {"nick": nick, "free": True}
    except Exception as e:
        return {"nick": nick, "free": None, "error": str(e)}

@app.get("/")
def read_root():
    return {"status": "Web Service is running"}

if __name__ == "__main__":
    # Render предоставляет порт через переменную окружения PORT
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
