import telebot
import requests
import json
import os
import threading
from flask import Flask, request

# ✅ Secure bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 📂 Hosted JSON file
JSON_URL = "https://sudeepnew123.github.io/Anime-provideer-/anime.json"
WEBHOOK_URL = "https://anime22.onrender.com"  # Replace with your Render domain
LOG_FILE = "downloads.json"

def get_anime_data():
    try:
        res = requests.get(JSON_URL)
        return res.json()
    except:
        return {}

def log_user_download(anime_name, username):
    logs = {}
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            logs = json.load(f)
    if anime_name not in logs:
        logs[anime_name] = []
    if username not in logs[anime_name]:
        logs[anime_name].append(username)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    first_name = message.from_user.first_name or ""
    username = message.from_user.username or f"id:{user_id}"

    # 🔘 Join button
    markup = telebot.types.InlineKeyboardMarkup()
    join_btn = telebot.types.InlineKeyboardButton("➕ Join Group", url="https://t.me/FOREVERFRANDS")
    markup.add(join_btn)

    welcome_msg = bot.send_message(
        chat_id,
        "👋 Welcome to Anime Provider Bot!\n\n📥 To access anime links, please join our group first.",
        reply_markup=markup
    )

    # 🕒 After 10 seconds, thank you message
    def send_thank_and_delete():
        import time
        time.sleep(10)
        thank_msg = bot.send_message(
            chat_id,
            "✅ Thanks for joining! Now please send the anime name you want."
        )

        # 🗑️ Delete both messages after 2 minutes
        time.sleep(110)  # 10 + 110 = 120 (2 min)
        try:
            bot.delete_message(chat_id, welcome_msg.message_id)
            bot.delete_message(chat_id, thank_msg.message_id)
        except:
            pass

    threading.Thread(target=send_thank_and_delete).start()

    # 📣 Send message to GC
    try:
        group_msg = bot.send_message(
            -1002302837596,  # ✅ Replace with your group chat ID
            f"<b>🚀 {first_name} (@{username}) just started the Anime Bot!</b>",
            parse_mode="HTML"
        )

        # 🗑️ Delete GC message after 2 min
        def delete_group_msg():
            import time
            time.sleep(120)
            try:
                bot.delete_message(-1002302837596, group_msg.message_id)
            except:
                pass

        threading.Thread(target=delete_group_msg).start()
    except:
        pass  # In case bot is not in group or no permission

@bot.message_handler(func=lambda m: True)
def handle_query(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"id:{user_id}"

    query = message.text.strip().lower()
    data = get_anime_data()

    for anime_id, anime in data.items():
        if query in anime_id.lower() or any(query in kw.lower() for kw in anime.get("keywords", [])):
            text = f"🎬 <b>{anime['title']}</b>\n📝 {anime['desc']}\n\n" \
                   f"📥 <a href='{anime['link_480p']}'>480p</a> | <a href='{anime['link_720p']}'>720p</a>"

            # 👇 Send photo if available
            if "thumb" in anime:
                bot.send_photo(
                    message.chat.id,
                    photo=anime["thumb"],
                    caption=text,
                    parse_mode='HTML'
                )
            else:
                bot.send_message(
                    message.chat.id,
                    text,
                    parse_mode='HTML',
                    disable_web_page_preview=True
                )

            log_user_download(anime_id, f"@{username}")
            return

    bot.send_message(message.chat.id, "❌ Sorry, anime not found. Try another name.")
    
@app.route("/", methods=["POST"])
def receive_update():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/set_webhook", methods=["GET"])
def set_webhook():
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    return "Webhook set!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
