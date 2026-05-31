import asyncio
import random
import logging
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from telethon import TelegramClient
from telethon.errors import FloodWaitError, UsernameInvalidError, UsernameNotOccupiedError

API_ID   = 20776429
API_HASH = '9c8955cc52c6df7e7c18def50d3838eb'
BOT_TOKEN = '7253456538:AAHtQz0uC5ZoVFUkZ4653EzpZecoYGFq0Hg'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Telethon через бот-токен
client = TelegramClient('bot_session', API_ID, API_HASH)

# ── Генератор произносимых ников ──
VOWELS     = list("aeiou")
CONSONANTS = list("bcdfghjklmnprstvwxyz")
SOFT_PAIRS = [
    'ar','er','or','an','en','on','al','el','ol',
    'ra','re','ro','na','ne','no','la','le','lo',
    'ma','me','mo','sa','se','so','ta','te','to',
    'va','ve','vo','ka','ke','ko','da','de','do',
    'ba','be','bo','fa','fe','fo','ga','ge','go',
]

def syllable():
    c = random.choice(CONSONANTS)
    v = random.choice(VOWELS)
    return c+v if random.random() < 0.5 else c+v+random.choice(CONSONANTS)

def generate_nick(length: int = 5) -> str:
    for _ in range(100):
        nick = ""
        while len(nick) < length:
            if random.random() < 0.4 and len(nick)+2 <= length:
                nick += random.choice(SOFT_PAIRS)
            else:
                s = syllable()
                if len(nick)+len(s) <= length:
                    nick += s
                elif length - len(nick) == 1:
                    nick += random.choice(VOWELS)
                else:
                    break
        if len(nick) == length:
            return nick
    n = ""
    for i in range(length):
        n += CONSONANTS[random.randint(0,len(CONSONANTS)-1)] if i%2==0 else VOWELS[random.randint(0,len(VOWELS)-1)]
    return n

# ── Проверка Fragment (продаётся ли ник) ──
async def check_fragment(nick: str) -> dict:
    """
    Возвращает:
      {"on_sale": True,  "price": "500 TON"}  — выставлен на продажу
      {"on_sale": False, "price": None}        — не на продаже
      {"on_sale": None,  "price": None}        — ошибка запроса
    """
    try:
        url = f"https://fragment.com/username/{nick}"
        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=6) as hc:
            r = await hc.get(url, headers=headers)
        text = r.text.lower()

        if "buy for" in text or "place a bid" in text or "auction" in text:
            # Пробуем вытащить цену
            import re
            price_match = re.search(r'([\d,]+)\s*ton', r.text, re.IGNORECASE)
            price = price_match.group(0) if price_match else "?"
            return {"on_sale": True, "price": price}

        if "is available" in text:
            return {"on_sale": False, "price": None}

        if "taken" in text or "unavailable" in text:
            return {"on_sale": False, "price": None}

        return {"on_sale": False, "price": None}
    except Exception as e:
        logger.warning(f"Fragment check error for {nick}: {e}")
        return {"on_sale": None, "price": None}

# ── Эндпоинты ──
@app.get("/health")
async def health():
    return {"status": "ok", "connected": client.is_connected()}

@app.get("/check")
async def check_nick(nick: str = None, length: int = 5):
    if not nick:
        nick = generate_nick(length)

    # 1. Проверяем через Telegram API — занят ли ник
    telegram_free = False
    try:
        await client.get_entity(nick)
        telegram_free = False   # нашли — занят
    except (ValueError, UsernameNotOccupiedError):
        telegram_free = True    # не нашли — свободен
    except UsernameInvalidError:
        return {"nick": nick, "free": None, "on_sale": None, "price": None, "reason": "invalid"}
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds + 1)
        return {"nick": nick, "free": None, "on_sale": None, "price": None, "reason": "flood_wait"}
    except Exception as e:
        logger.error(f"Telegram check error: {e}")
        return {"nick": nick, "free": None, "on_sale": None, "price": None, "reason": str(e)}

    # 2. Проверяем Fragment — не продаётся ли
    fragment = await check_fragment(nick)

    return {
        "nick":     nick,
        "free":     telegram_free,          # True = свободен в Telegram
        "on_sale":  fragment["on_sale"],    # True = выставлен на Fragment
        "price":    fragment["price"],      # "500 TON" или None
    }

@app.on_event("startup")
async def startup():
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ Бот запущен через токен!")

@app.on_event("shutdown")
async def shutdown():
    await client.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
