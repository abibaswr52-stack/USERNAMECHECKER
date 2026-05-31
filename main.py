import asyncio
import random
import logging
import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError, UsernameInvalidError, UsernameNotOccupiedError

API_ID     = 20776429
API_HASH   = '9c8955cc52c6df7e7c18def50d3838eb'
BOT_TOKEN  = '7253456538:AAHtQz0uC5ZoVFUkZ4653EzpZecoYGFq0Hg'
WEBAPP_URL = "https://usernamechecker-o2h7.vercel.app"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Два клиента:
# bot_client  — для приёма /start и отправки сообщений (бот)
# user_client — для проверки юзернеймов (юзер-сессия)
bot_client  = TelegramClient('bot_session',  API_ID, API_HASH)
user_client = TelegramClient('user_session', API_ID, API_HASH)

# ── /start — приветствие ──
@bot_client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    sender = await event.get_sender()
    name = getattr(sender, 'first_name', None) or getattr(sender, 'username', None) or "пользователь"

    buttons = bot_client.build_reply_markup([
        [{"text": "🔎 Открыть Nick Checker", "url": WEBAPP_URL}]
    ])

    await event.respond(
        f"Привет, **{name}** 👋\n\n"
        f"Добро пожаловать в **Nick Checker**.\n\n"
        f"Я — ваш инструмент для поиска свободных юзернеймов в Telegram. "
        f"Чтобы начать проверку, просто запустите Mini App через кнопку «Открыть» внизу.\n\n"
        f"🚀 _Система полностью готова к работе._",
        buttons=buttons
    )

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

# ── Проверка Fragment ──
async def check_fragment(nick: str) -> dict:
    try:
        import re
        url = f"https://fragment.com/username/{nick}"
        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=6) as hc:
            r = await hc.get(url, headers=headers)
        text = r.text.lower()
        if "buy for" in text or "place a bid" in text or "auction" in text:
            price_match = re.search(r'([\d,]+)\s*ton', r.text, re.IGNORECASE)
            price = price_match.group(0) if price_match else "?"
            return {"on_sale": True, "price": price}
        return {"on_sale": False, "price": None}
    except Exception as e:
        logger.warning(f"Fragment check error for {nick}: {e}")
        return {"on_sale": None, "price": None}

# ── Эндпоинты ──
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "bot_connected":  bot_client.is_connected(),
        "user_connected": user_client.is_connected(),
    }

@app.get("/check")
async def check_nick(nick: str = None, length: int = 5):
    if not nick:
        nick = generate_nick(length)

    # Проверка через user_client (юзер-сессия умеет резолвить юзернеймы)
    telegram_free = False
    try:
        await user_client.get_entity(nick)
        telegram_free = False
    except (ValueError, UsernameNotOccupiedError):
        telegram_free = True
    except UsernameInvalidError:
        return {"nick": nick, "free": None, "on_sale": None, "price": None, "reason": "invalid"}
    except FloodWaitError as e:
        await asyncio.sleep(e.seconds + 1)
        return {"nick": nick, "free": None, "on_sale": None, "price": None, "reason": "flood_wait"}
    except Exception as e:
        logger.error(f"Telegram check error: {e}")
        return {"nick": nick, "free": None, "on_sale": None, "price": None, "reason": str(e)}

    fragment = await check_fragment(nick)

    return {
        "nick":    nick,
        "free":    telegram_free,
        "on_sale": fragment["on_sale"],
        "price":   fragment["price"],
    }

@app.on_event("startup")
async def startup():
    # Бот — через токен (для /start и сообщений)
    await bot_client.start(bot_token=BOT_TOKEN)
    logger.info("✅ Бот запущен!")

    # Юзер — через сессию (для проверки юзернеймов)
    await user_client.start()
    logger.info("✅ Юзер-клиент запущен!")

    asyncio.get_event_loop().create_task(bot_client.run_until_disconnected())

@app.on_event("shutdown")
async def shutdown():
    await bot_client.disconnect()
    await user_client.disconnect()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
