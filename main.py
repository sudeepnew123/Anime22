import telebot
import requests
import json
import os
from flask import Flask, request

# ✅ Secure bot token from environment
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 📂 Hosted JSON file
JSON_URL = "https://sudeepnew123.github.io/Anime-provideer-/anime.json"
GROUP_CHAT_ID = -1002302837596
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

def is_user_joined(user_id):
    try:
        status = bot.get_chat_member(GROUP_CHAT_ID, user_id).status
        return status in ["member", "administrator", "creator"]
    except:
        return False

@bot.message_handler(commands=["start"])
def start(message):
    markup = telebot.types.InlineKeyboardMarkup()
    join_btn = telebot.types.InlineKeyboardButton("➕ Join Group", url="https://t.me/YourGroupUsername")
    markup.add(join_btn)
    bot.send_message(
        message.chat.id,
        "👋 Welcome to Anime Provider Bot!\n\n📥 To access anime links, please join our group first.",
        reply_markup=markup
    )

@bot.message_handler(func=lambda m: True)
def handle_query(message):
    user_id = message.from_user.id
    username = message.from_user.username or f"id:{user_id}"
    if not is_user_joined(user_id):
        bot.send_message(message.chat.id, "❌ Please join the group first to access anime content.")
        return

    query = message.text.strip().lower()
    data = get_anime_data()

    for anime_id, anime in data.items():
        if query in anime_id.lower() or any(query in kw.lower() for kw in anime.get("keywords", [])):
            text = f"🎬 <b>{anime['title']}</b>\n📝 {anime['desc']}\n\n" \
                   f"📥 <a href='{anime['link_480p']}'>480p</a> | <a href='{anime['link_720p']}'>720p</a>"
            bot.send_message(message.chat.id, text, parse_mode='HTML', disable_web_page_preview=True)
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
