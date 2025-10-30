import os
import requests
from io import BytesIO
import telebot
from flask import Flask
import threading

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("API_KEY")
API_URL = os.getenv("API_URL", "https://api-xtsc.onrender.com/download")
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise SystemExit("❌ BOT_TOKEN topilmadi — Render environment variables ni tekshir!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask(__name__)

@app.route("/")
def home():
    return {"status": "ok", "message": "✅ Bot ishlayapti!"}

def download_media(url):
    headers = {"x-api-key": API_KEY} if API_KEY else {}
    try:
        r = requests.get(API_URL, headers=headers, params={"url": url}, timeout=25)
        r.raise_for_status()
        data = r.json()
        if data.get("status") != "ok":
            return []
        return data.get("media", [])
    except Exception as e:
        print("API xato:", e)
        return []

@bot.message_handler(commands=['start', 'help'])
def start(msg):
    bot.reply_to(msg, f"👋 Salom, <b>{msg.from_user.first_name}</b>!\nMenga Instagram yoki Pinterest link yubor — men media yuboraman 📥")

@bot.message_handler(func=lambda m: m.text and m.text.startswith("http"))
def handle_link(msg):
    url = msg.text.strip()
    if "instagram.com" not in url and "pinterest.com" not in url:
        bot.reply_to(msg, "⚠️ Faqat Instagram yoki Pinterest link yubor!")
        return

    loading = bot.reply_to(msg, "🔄 Yuklanmoqda...")

    media_list = download_media(url)
    if not media_list:
        bot.edit_message_text("❌ Media topilmadi yoki post private.", chat_id=msg.chat.id, message_id=loading.message_id)
        return

    for item in media_list:
        media_url = item.get("url", "").replace("&amp;", "&")
        if not media_url:
            continue
        try:
            res = requests.get(media_url, timeout=30)
            if res.status_code != 200:
                bot.send_message(msg.chat.id, "❌ Faylni yuklab bo‘lmadi.")
                continue

            file = BytesIO(res.content)
            if item.get("type") == "video":
                file.name = "video.mp4"
                bot.send_video(msg.chat.id, video=file, caption="🎥 Video yuklandi ✅")
            else:
                file.name = "image.jpg"
                bot.send_photo(msg.chat.id, photo=file, caption="🖼️ Rasm yuklandi ✅")
        except Exception as e:
            print("Yuborish xatosi:", e)
            bot.send_message(msg.chat.id, "❌ Media yuborishda xato yuz berdi.")

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

def run_bot():
    bot.infinity_polling()

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
