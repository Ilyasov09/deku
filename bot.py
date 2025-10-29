import os
import asyncio
import threading
import requests
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command
from flask import Flask, request

# --- Asosiy sozlamalar ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://api-xtsc.onrender.com/download")
API_KEY = os.getenv("API_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

app = Flask(__name__)

# --- FUNKSIYA: media yuklash ---
def download_media(url):
    headers = {"x-api-key": API_KEY}
    params = {"url": url}
    try:
        res = requests.get(API_URL, headers=headers, params=params, timeout=25)
        data = res.json()
        if data.get("status") != "ok":
            return None
        return data.get("media", [])
    except Exception as e:
        print("API xato:", e)
        return None


# --- HANDLER: Instagram yoki Pinterest link yuborilgan ---
@router.message(lambda msg: msg.text and ("instagram.com" in msg.text.lower() or "pinterest.com" in msg.text.lower()))
async def handle_media(msg: types.Message):
    url = msg.text.strip()
    media = download_media(url)

    if not media:
        await msg.reply("⚠️ Media topilmadi yoki post private bo‘lishi mumkin.")
        return

    # Guruh yoki shaxsiy chat
    if msg.chat.type in ["group", "supergroup"]:
        username = f"@{msg.from_user.username}" if msg.from_user.username else msg.from_user.full_name
        caption = f"{username} yuborgan media 🎥"
    else:
        caption = "Mana yuklab oling 👇"

    # Media yuborish
    for item in media:
        try:
            if item["type"] == "video":
                await msg.reply_video(item["url"], caption=caption)
            elif item["type"] == "image":
                await msg.reply_photo(item["url"], caption=caption)
        except Exception as e:
            await msg.reply(f"❌ Media yuborishda xato: {e}")


# --- HANDLER: "deku" so‘ziga javob ---
@router.message(lambda msg: msg.text and msg.text.lower() in ["deku", "деку"])
async def react_deku(msg: types.Message):
    try:
        await msg.reply("💚")
    except:
        pass


# --- Flask route (Render uchun jonli tutish) ---
@app.route('/')
def home():
    return {"status": "ok", "message": "DEKU InstaPin bot ishlayapti"}


# --- Asosiy ishga tushirish funksiyasi ---
async def main():
    print("🤖 Bot ishga tushmoqda...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Flask serverni parallel ravishda ishga tushuramiz
    def run_flask():
        app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))

    threading.Thread(target=run_flask).start()

    # Asosiy asyncio loopni ishga tushuramiz
    asyncio.run(main())
