import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from telethon import TelegramClient
from telethon.errors import UsernameInvalidError, UsernameNotOccupiedError, FloodWaitError

API_ID = 20776429
API_HASH = '9c8955cc52c6df7e7c18def50d3838eb'

# Инициализация клиента
client = TelegramClient('checker_session', API_ID, API_HASH)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код при старте
    await client.start()
    print("✅ Telethon клиент запущен")
    yield
    # Код при выключении
    await client.disconnect()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok", "connected": client.is_connected()}

@app.get("/check")
async def check_nick(nick: str):
    try:
        # Убираем @, если пользователь прислал с ним
        nick = nick.replace("@", "")
        await client.get_entity(nick)
        return {"nick": nick, "free": False}
    except (ValueError, UsernameNotOccupiedError):
        return {"nick": nick, "free": True}
    except UsernameInvalidError:
        return {"nick": nick, "free": None, "reason": "invalid"}
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds + 1)
        return {"nick": nick, "free": None, "reason": "flood"}
    except Exception as e:
        return {"nick": nick, "free": None, "error": str(e)}
