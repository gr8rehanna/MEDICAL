from pyrogram import Client, filters
from pyrogram.enums import ChatAction, ParseMode
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import requests
from gtts import gTTS
import os
from config import API_ID, API_HASH, BOT_TOKEN, BASE_URL, API_KEY, SUPPORT_LINK, AI_MODEL

# Initialize the bot client
app = Client("message_handler_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Dictionary to store replies temporarily based on message IDs
message_responses = {}

# Function to convert text to speech and send it as an audio file
async def text_to_speech(text, chat_id):
    tts = gTTS(text=text, lang='en')
    file_path = 'audio.mp3'
    tts.save(file_path)
    await app.send_audio(chat_id=chat_id, audio=file_path)
    os.remove(file_path)  # Clean up the temporary audio file

# Handler for the /start command
@app.on_message(filters.command("start"))
async def start_command(bot, message):
    try:
        await message.reply_video(
            video="https://files.catbox.moe/qdtfhq.mp4",
            caption=(
                "🌟 Welcome to Healix AI – Your Virtual Health Companion! 🌟\n\n👨‍⚕️ What Can I Do?\n"
                "🔹 Analyze your symptoms\n"
                "🔹 Predict potential diseases\n🔹 Provide remedies, precautions, and wellness tips\n\n"
                "✨ How Does It Work?\n✅ Simple & Quick! Just type in your symptoms, and I'll provide accurate, AI-powered health insights instantly!\n\n"
                "Let’s make your health journey smarter, faster, and easier! 💖\n\n🌐 Stay Connected with Us!\n[🌍 Website](https://healixai.tech) | [💬 Telegram](https://t.me/HealixAi) | [🐦 Twitter](https://x.com/Healix__AI)."
            ),
            parse_mode=ParseMode.MARKDOWN
        )
    except Exception as e:
        print(f"Error in /start command: {e}")
        await message.reply_text("❍ ᴇʀʀᴏʀ: Unable to process the command.")

# Handler for the /doctor command (group)
@app.on_message(filters.command("doctor") & filters.group)
async def fetch_med_info(client, message):
    query = " ".join(message.command[1:])  # Extract the query after the command
    if not query:
        await message.reply_text("Please provide a medical query to ask.")
        return

    await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    payload = {
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ],
        "stream": False,
        "model": AI_MODEL
    }
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "okai.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(BASE_URL, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            reply = data.get("response", "Sorry, I couldn't fetch the data.")
        else:
            reply = "Failed to fetch data from the API."
    except Exception as e:
        reply = f"An error occurred: {e}"

    message_responses[message.id] = reply
    await message.reply_text(
        reply,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Convert to TTS", callback_data=f'tts_{message.id}')]
        ])
    )

# Handler for private message queries (DM/PM), ignoring commands
@app.on_message(filters.private & ~filters.command(["start", "doctor"]))
async def handle_private_query(client, message):
    query = message.text.strip()
    if not query:
        await message.reply_text("Please provide a medical query.")
        return

    await client.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    payload = {
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ],
        "stream": False,
        "model": AI_MODEL
    }
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "okai.p.rapidapi.com",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(BASE_URL, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            reply = data.get("response", "Sorry, I couldn't fetch the data.")
        else:
            reply = "Failed to fetch data from the API."
    except Exception as e:
        reply = f"An error occurred: {e}"

    message_responses[message.id] = reply
    await message.reply_text(
        reply,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Convert to TTS", callback_data=f'tts_{message.id}')]
        ])
    )

# Handler for button click (Convert to TTS)
@app.on_callback_query(filters.regex('^tts_'))
async def on_button_click(client, callback_query):
    message_id = int(callback_query.data.split('_')[1])
    text = message_responses.get(message_id, "No data found.")
    await text_to_speech(text, callback_query.message.chat.id)
    await callback_query.answer()
    if message_id in message_responses:
        del message_responses[message_id]

# Run the bot
if __name__ == "__main__":
    print("Bot is running...")
    app.run()
