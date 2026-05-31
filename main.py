import os
import uvicorn
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from telethon import TelegramClient
from telethon.errors import UsernameInvalidError, UsernameNotOccupiedError

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ВАШИ ДАННЫЕ ---
API_ID = 20776429
API_HASH = '9c8955cc52c6df7e7c18def50d3838eb'
# Вставьте сюда токен, полученный от @BotFather
BOT_TOKEN = '7253456538:AAHtQz0uC5ZoVFUkZ4653EzpZecoYGFq0Hg' 

app = FastAPI()

# Разрешаем все запросы (для Mini App это необходимо)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация клиента (имя сессии теперь 'bot')
client = TelegramClient('bot', API_ID, API_HASH)

@app.on_event("startup")
async def startup_event():
    logger.info("Запуск Telegram бота через токен...")
    await client.start(bot_token=BOT_TOKEN)
    logger.info("✅ Бот успешно запущен!")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/check")
async def check_nick(nick: str):
    try:
        nick = nick.replace("@", "").strip()
        # Для ботов метод get_entity работает отлично
        await client.get_entity(nick)
        return {"nick": nick, "free": False}
    except (ValueError, UsernameNotOccupiedError):
        return {"nick": nick, "free": True}
    except Exception as e:
        logger.error(f"Ошибка проверки {nick}: {e}")
        return {"nick": nick, "free": None, "error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
