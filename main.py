
import logging
import os
import asyncio
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiohttp import web

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in Secrets!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Short concise welcome text with famous quote ---
WELCOME_RU = (
    '"ИИ не заменит тебя. Заменит человек с ИИ."\n'
    "— CEO NVIDIA\n\n"
    "Я Даша, автор «Разум будущего» 👋\n"
    "Как не остаться за бортом и заработать в мире AI, оставаясь собой.\n\n"
    "13 000+ уже скачали. Забирай бесплатно 👇"
)

WELCOME_EN = (
    '"AI will not replace you. A person using AI will."\n'
    "— NVIDIA\n\n"
    "I'm Dasha, author of 'Mind of the Future'.\n"
    "How to stay relevant and earn in the AI world — without losing yourself.\n\n"
    "Pick a language and get it free 👇"
)

WELCOME_ZH = (
    '"AI不会取代你，但会使用AI的人会。"\n'
    "— 英伟达\n\n"
    "我是达莎，《未来心智》作者。\n"
    "如何在AI时代不被抛弃，并赚钱，保持自我。\n\n"
    "免费领取 👇"
)

# Keyboard
def get_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Russian"), KeyboardButton(text="English")],
            [KeyboardButton(text="Chinese")]
        ],
        resize_keyboard=True
    )

BOOKS = {
    "Russian": "books/Razum_book_RU.pdf",
    "English": "books/Razum_book_EN.pdf",
    "Chinese": "books/Razum_book_ZH.pdf",
    # fallback names
    "RU": "books/razum_budushego_editorial_v3.pdf",
    "EN": "books/Razum_book_EN.pdf",
    "ZH": "books/razum_budushego_zh.pdf",
}

WELCOME_PHOTO = Path("books/welcome_brain.jpg")
# also check alternative paths
if not WELCOME_PHOTO.exists():
    for alt in ["welcome_brain.jpg", "books/welcome.jpg", "attached_assets/welcome.jpg"]:
        if Path(alt).exists():
            WELCOME_PHOTO = Path(alt)
            break

@dp.message(CommandStart())
async def cmd_start(message: Message):
    # Try to send photo with caption
    try:
        if WELCOME_PHOTO.exists():
            photo = FSInputFile(WELCOME_PHOTO)
            await message.answer_photo(
                photo=photo,
                caption=WELCOME_RU,
                reply_markup=get_keyboard()
            )
        else:
            await message.answer(WELCOME_RU, reply_markup=get_keyboard())
    except Exception as e:
        logger.error(f"Photo send failed: {e}")
        await message.answer(WELCOME_RU, reply_markup=get_keyboard())

@dp.message(F.text.in_(["Russian", "English", "Chinese", "RU", "EN", "ZH", "🇷🇺 Русский", "🇬🇧 English", "🇪🇸 中文"]))
async def send_book(message: Message):
    lang_map = {
        "Russian": "books/Razum_book_RU.pdf",
        "English": "books/Razum_book_EN.pdf",
        "Chinese": "books/Razum_book_ZH.pdf",
    }
    # map also old names
    if message.text in BOOKS:
        path = BOOKS[message.text]
    else:
        path = lang_map.get(message.text)
    
    # Try to find file in multiple places
    possible_paths = [
        path,
        f"books/{Path(path).name}",
        f"books/razum_budushego_editorial_v3.pdf" if "Russian" in message.text or "RU" in message.text else None,
        f"books/Razum_book_EN.pdf" if "English" in message.text else None,
        f"books/Razum_book_ZH.pdf" if "Chinese" in message.text else None,
    ]
    possible_paths = [p for p in possible_paths if p]
    
    file_path = None
    for p in possible_paths:
        if Path(p).exists():
            file_path = p
            break
    
    if not file_path:
        await message.answer("Файл не найден на сервере 😢 Напиши @razum_book")
        return
    
    captions = {
        "Russian": "Держи! 🤍 Читай где угодно. Если зацепит — напиши мне @razum_book",
        "English": "Here you go! 🤍 Read anywhere. If it hits you — DM me @razum_book",
        "Chinese": "给你! 🤍 随时随地阅读。如果喜欢 — 联系我 @razum_book"
    }
    cap = captions.get(message.text, "Вот твоя книга 🤍")
    
    try:
        doc = FSInputFile(file_path)
        await message.answer_document(document=doc, caption=cap)
    except Exception as e:
        logger.error(f"Send doc error: {e}")
        await message.answer(f"Ошибка отправки: {e}")

# --- Keep alive web server for UptimeRobot ---
async def health_handler(request):
    return web.Response(text="Bot is alive! @Razum_bot running 24/7")

async def start_webserver():
    app = web.Application()
    app.router.add_get('/', health_handler)
    app.router.add_get('/health', health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    logger.info(f"Web server started on port {port}")
    while True:
        await asyncio.sleep(3600)

async def run_bot():
    token = BOT_TOKEN
    # start webserver as background task
    asyncio.create_task(start_webserver())
    logger.info("Starting bot polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run_bot())
