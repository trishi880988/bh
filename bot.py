from pyrogram import Client, filters, InlineKeyboardMarkup, InlineKeyboardButton
import re
import requests
import logging

# Enable logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Client(
    "terabox_stream_bot",
    api_id=27893267,
    api_hash="7dd7e4a227b0ee849a154b682b5f4cb1",
    bot_token="7750327083:AAFa9UBrMxmXcF5Wb_QriA8jYOmIZeZSVdo"
)

def extract_terabox_id(url):
    """Extract file ID from Terabox URL"""
    pattern = r'terabox\.app\/(?:s\/)?([a-zA-Z0-9_-]+)'
    match = re.search(pattern, url)
    return match.group(1) if match else None

@app.on_message(filters.command("start"))
async def start(client, message):
    try:
        await message.reply("""🎬 **Terabox Video Streamer Bot**
        
Send me any Terabox video link and I'll generate a streamable URL!
No API keys required!""")
        logger.info(f"Start command received from {message.from_user.id}")
    except Exception as e:
        logger.error(f"Start command error: {e}")

@app.on_message(filters.text & ~filters.command("start"))
async def handle_link(client, message):
    try:
        url = message.text.strip()
        if "terabox.app" not in url:
            await message.reply("❌ Please send a valid Terabox link")
            return

        msg = await message.reply("🔍 Extracting video...")
        file_id = extract_terabox_id(url)
        
        if not file_id:
            await msg.edit("❌ Invalid Terabox URL format")
            return
            
        stream_url = f"https://www.terabox.app/shared/video?file_id={file_id}"
        
        # Verify the link actually works
        response = requests.head(stream_url, timeout=10)
        if response.status_code != 200:
            await msg.edit("❌ Couldn't generate streamable link (Terabox may have blocked this)")
            return

        await msg.edit(
            f"🎥 **Stream This Video**\n\n"
            f"🔗 `{stream_url}`\n\n"
            "Open in VLC/MX Player or click below:",
            disable_web_page_preview=False,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Play Now", url=stream_url)],
                [InlineKeyboardButton("📥 Download", callback_data=f"dl_{file_id}")]
            ])
        )
        logger.info(f"Generated stream URL for {file_id}")
        
    except requests.Timeout:
        await message.reply("⌛ Terabox server is taking too long to respond")
    except Exception as e:
        logger.error(f"Error handling link: {e}")
        await message.reply(f"⚠️ An error occurred: {str(e)}")

if __name__ == "__main__":
    print("Bot is running...")
    app.run()
