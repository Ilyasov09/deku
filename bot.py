import os
import requests
from io import BytesIO
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from flask import Flask
import threading
import asyncio

# --- Config ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL", "https://api-xtsc.onrender.com/download")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# --- Flask app (Render jonli tutish uchun) ---
app = Flask(__name__)

@app.route('/')
def home():
    return {"status": "ok", "message": "💚 DEKU InstaPin bot ishlayapti"}

# --- Media yuklash funksiyasi ---
def download_media(url):
    headers = {"x-api-key": API_KEY}
    params = {"url": url}
    try:
        r = requests.get(API_URL, headers=headers, params=params, timeout=25)
        data = r.json()
        if data.get("status") != "ok":
            return []
        return data["media"]
    except Exception as e:
        print("❌ API bilan bog'lanishda xato:", e)
        return []

# --- START komandasi ---
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
        await msg.answer("❌ Media topilmadi yoki post private.")
        return

    for item in media_list:
        try:
            # Faylni yuklab olish
            file_data = requests.get(item["url"], stream=True, timeout=30)
            file_bytes = BytesIO(file_data.content)
            file_bytes.name = "media.mp4" if item["type"] == "video" else "image.jpg"

            if item["type"] == "video":
                await msg.answer_video(video=file_bytes, caption="🎥 Video tayyor!")
            elif item["type"] == "image":
                await msg.answer_photo(photo=file_bytes, caption="🖼️ Rasm tayyor!")

        except Exception as e:
            await msg.answer(f"❌ Media yuborishda xato: {e}")

# --- Flask serverni alohida oqimda ishga tushirish ---
def run_flask():
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

# --- Asosiy ishga tushirish ---
if __name__ == "__main__":
    print("🤖 Bot ishga tushmoqda...")
    threading.Thread(target=run_flask).start()
    asyncio.run(dp.start_polling(bot))
