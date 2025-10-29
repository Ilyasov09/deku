import os
import requests
import telebot
from telebot import types
from flask import Flask
from threading import Thread

# 🔐 Tokenni Render environment'dan olamiz
TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable topilmadi! Render'da qo‘shishni unutmang.")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# 💬 Flask jonli javobi (UptimeRobot uchun)
@app.route('/')
def home():
    return "✅ DEKU bot ishlayapti!", 200


# 🎬 Instagram videoni yuklab olish funksiyasi
def get_instagram_video(insta_url):
    try:
        api_url = f"https://api.terrabox.tech/insta?url={insta_url}"
        response = requests.get(api_url)
        if response.status_code == 200:
            data = response.json()
            if data.get("url"):
                return data["url"]
        return None
    except Exception as e:
        print("❌ API xato:", e)
        return None


# 🚀 /start komandasi
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message,
                 "👋 Salom! Men DEKU botman.\n"
                 "Menga Instagram link yubor, men esa videoni yuboraman 🎥\n\n"
                 "Guruhda ishlasam: foydalanuvchi video yuborsa, caption qo‘shaman 💚")


# 🎯 “deku” yoki “DEKU” so‘zlariga reaksiya
@bot.message_handler(func=lambda msg: msg.text and msg.text.lower() in ["deku", "деку"])
def react_to_deku(message):
    try:
        bot.set_message_reaction(chat_id=message.chat.id,
                                 message_id=message.message_id,
                                 reaction=[types.ReactionTypeEmoji("💚")])
    except Exception as e:
        print("Reaksiya qo‘shishda xato:", e)


# 🧩 Asosiy xabar handler
@bot.message_handler(func=lambda msg: True)
def handle_message(message):
    text = message.text.strip()

    # Agar Instagram link bo‘lsa
    if "instagram.com" in text:
        video_url = get_instagram_video(text)
        if video_url:
            if message.chat.type in ["group", "supergroup"]:
                caption = f"🎬 @{message.from_user.username or message.from_user.first_name} video yubordi!"
                bot.reply_to(message, "⏬ Yuklanmoqda, biroz kuting...")
                bot.send_video(message.chat.id, video=video_url, caption=caption)
            else:
                bot.send_message(message.chat.id, "⏬ Yuklanmoqda...")
                bot.send_video(message.chat.id, video=video_url, caption="🎬 Mana siz so‘ragan video!")
                # 💚 Reaksiya
                try:
                    bot.set_message_reaction(chat_id=message.chat.id,
                                             message_id=message.message_id,
                                             reaction=[types.ReactionTypeEmoji("💚")])
                except Exception:
                    pass
        else:
            bot.reply_to(message, "❌ Video yuklab bo‘lmadi. Iltimos, haqiqiy Instagram link yuboring.")
    else:
        # Boshqa xabarlar uchun javob bermaslik
        pass


# 🧵 Flask va botni birga ishga tushirish
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))


def run_bot():
    bot.polling(none_stop=True)


if __name__ == "__main__":
    Thread(target=run_flask).start()
    Thread(target=run_bot).start()
