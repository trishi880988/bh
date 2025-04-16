from pyrogram import Client, filters
import re
import requests

app = Client(
    "terabox_stream_bot",
    api_id=27893267,  # Replace with your API ID
    api_hash="7dd7e4a227b0ee849a154b682b5f4cb1",  # Replace with your API HASH
    bot_token="7750327083:AAFa9UBrMxmXcF5Wb_QriA8jYOmIZeZSVdo"  # Replace with your bot token
)

def extract_terabox_id(url):
    """Extract file ID from Terabox URL"""
    pattern = r'terabox\.app\/(?:s\/)?([a-zA-Z0-9_-]+)'
    match = re.search(pattern, url)
    return match.group(1) if match else None

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply("""🎬 **Terabox Video Streamer Bot**
    
Send me any Terabox video link and I'll generate a streamable URL!

No API keys required!""")

@app.on_message(filters.text & ~filters.command("start"))
async def handle_link(client, message):
    url = message.text.strip()
    if "terabox.app" not in url:
        return await message.reply("Please send a valid Terabox link")
    
    try:
        msg = await message.reply("🔍 Extracting video...")
        
        # Extract direct stream URL (works without API)
        file_id = extract_terabox_id(url)
        if not file_id:
            return await msg.edit("Invalid Terabox URL format")
            
        stream_url = f"https://www.terabox.app/shared/video?file_id={file_id}"
        
        await msg.edit(
            f"🎥 **Stream This Video**\n\n"
            f"🔗 {stream_url}\n\n"
            "Open in any video player that supports direct links",
            disable_web_page_preview=False,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("▶️ Play Now", url=stream_url)],
                [InlineKeyboardButton("📥 Download", callback_data=f"dl_{file_id}")]
            ])
        )
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

app.run()
