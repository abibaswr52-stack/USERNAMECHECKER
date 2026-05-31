import os
import random
import logging
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from telethon import TelegramClient
from telethon.errors import FloodWaitError, UsernameInvalidError

# --- ВСТАВЬ СЮДА СВОИ ДАННЫЕ ---
API_ID = 20776429 
API_HASH = '9c8955cc52c6df7e7c18def50d3838eb'
BOT_TOKEN = '7253456538:AAHtQz0uC5ZoVFUkZ4653EzpZecoYGFq0Hg' 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
client = TelegramClient('bot_session', API_ID, API_HASH)

# Генератор 5-6-7 символьных ников
def generate_nick():
    v = "aeiou"
    c = "bcdfghjklmnprstvw"
    s = "lnrm"
    # Случайная длина 5, 6 или 7
    length = random.choice([5, 6, 7])
    nick = "".join(random.choice(c) + random.choice(v) for _ in range(length // 2))
    if length % 2 != 0: nick += random.choice(c)
    return nick

# Проверка Fragment
def check_fragment(nick):
    try:
        url = f"https://fragment.com/username/{nick}"
        r = requests.get(url, timeout=3)
        if "is available" in r.text.lower(): return "FREE"
        if "taken" in r.text.lower(): return "TAKEN"
        return "UNKNOWN"
    except: return "ERROR"

@app.get("/check")
async def check_nick(nick: str = None):
    if not nick: nick = generate_nick()
    
    try:
        await client.get_entity(nick)
        # Если занят — проверяем статус на Fragment
        return {"nick": nick, "free": False, "fragment": check_fragment(nick)}
    except ValueError:
        return {"nick": nick, "free": True}
    except FloodWaitError as e:
        return {"error": "flood_wait", "seconds": e.seconds}
    except Exception:
        return {"error": "invalid_or_error"}

@app.on_event("startup")
async def startup():
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ Бот и Checker запущены!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
