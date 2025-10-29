import os
import requests
from io import BytesIO
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InputFile
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from flask import Flask
import threading
import asyncio
import logging

# --- Logging yoqamiz ---
logging.basicConfig(level=logging.INFO)

# --- Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL", "https://api-xtsc.onrender.com/download")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable topilmadi!")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- Flask app (Render uchun jonli tutish) ---
app = Flask(__name__)

@app.route('/')
def home():
    return {"status": "ok", "message": "💚 DEKU InstaPin bot ishlayapti"}

# --- Media yuklash funksiyasi ---
def download_media(url: str):
    """API'dan media URL'larni oladi"""
    headers = {"x-api-key": API_KEY} if API_KEY else {}
    params = {"url": url}
    try:
        response = requests.get(API_URL, headers=headers, params=params, timeout=25)
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "ok":
            print("⚠️ API status:", data.get("status"))
            return []

        return data.get("media", [])
    except Exception as e:
        print("❌ API bilan bog‘lanishda xato:", e)
        return []

# --- /start komandasi ---
@dp.message(CommandStart())
async def start_handler(msg: Message):
    name = msg.from_user.first_name
    await msg.answer(
        f"👋 Salom, <b>{name}</b>!\n\n"
        "Men <b>Instagram</b> va <b>Pinterest</b> dan media yuklab bera olaman 📸🎥\n\n"
        "Menga shunchaki post yoki reel linkini yuboring 👇"
    )

# --- LINK tutuvchi handler ---
@dp.message(F.text.regexp(r"https?://"))
async def handle_link(msg: Message):
    url = msg.text.strip()

    if not any(x in url for x in ["instagram.com", "pinterest.com"]):
        await msg.answer("⚠️ Faqat Instagram yoki Pinterest linklarini yuboring.")
        return

    await msg.answer("🔍 Media yuklanmoqda, biroz kuting...")

    media_list = download_media(url)
    if not media_list:
        await msg.answer("❌ Media topilmadi yoki post private yoki API ishlamayapti.")
        return

    for item in media_list:
        try:
            media_url = item.get("url")
            media_type = item.get("type")

            if not media_url or media_type not in ["video", "image"]:
                continue

            # Faylni yuklab olish (telegram uchun to‘liq URL bo‘lishi kerak)
            response = requests.get(media_url, timeout=30)
            if response.status_code != 200:
                await msg.answer("❌ Faylni yuklab bo‘lmadi (URL xato).")
                continue

            file_bytes = BytesIO(response.content)
            file_bytes.name = "media.mp4" if media_type == "video" else "image.jpg"

            if media_type == "video":
                await msg.answer_video(InputFile(file_bytes), caption="🎥 Video tayyor!")
            else:
                await msg.answer_photo(InputFile(file_bytes), caption="🖼️ Rasm tayyor!")

        except Exception as e:
            logging.error(f"❌ Media yuborishda xato: {e}")
            await msg.answer("❌ Media yuborishda xato yuz berdi.")

# --- Flask serverni alohida oqimda ishga tushirish ---
def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

# --- Asosiy ishga tushirish ---
if __name__ == "__main__":
    print("🤖 Bot ishga tushmoqda...")
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(dp.start_polling(bot))
