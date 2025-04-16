import os
import re
import time
import requests
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from config import Config
from datetime import datetime

app = Client(
    "terabox_bot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)

# Developer information
DEVELOPER = "Bot Developed by GaURaV RaJpUT"
CAPTION = "@ytbr_67"
BOT_START_TIME = datetime.now()

def format_size(bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

def extract_terabox_id(url):
    pattern = r'terabox\.app\/(?:s\/)?([a-zA-Z0-9_-]+)'
    match = re.search(pattern, url)
    return match.group(1) if match else None

def get_direct_link(terabox_url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Cookie": Config.TERABOX_COOKIE
    }
    
    response = requests.get(terabox_url, headers=headers)
    if "errno" in response.text:
        raise Exception("Terabox error: Invalid cookie or link")
    
    download_token = re.search(r'download_token.*?"(.*?)"', response.text)
    if not download_token:
        raise Exception("Couldn't extract download token")
    
    file_id = extract_terabox_id(terabox_url)
    api_url = f"https://www.terabox.app/api/download?app_id=250528&web=1&channel=dubox&clienttype=0&jsToken={download_token.group(1)}"
    
    dl_response = requests.get(api_url, headers=headers)
    if dl_response.status_code != 200:
        raise Exception("Failed to get download link")
    
    return dl_response.json().get("dlink")

async def download_with_progress(client, message, url, file_path):
    start_time = time.time()
    downloaded = 0
    
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        total_size = int(r.headers.get('content-length', 0))
        
        with open(file_path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
                downloaded += len(chunk)
                
                # Update progress every 5 seconds
                if time.time() - start_time > 5:
                    speed = downloaded / (time.time() - start_time)
                    progress = (downloaded / total_size) * 100
                    
                    try:
                        await message.edit_text(
                            f"**Downloading...**\n\n"
                            f"▰ {progress:.2f}% Completed\n"
                            f"⚡ Speed: {format_size(speed)}/s\n"
                            f"📦 Size: {format_size(downloaded)} / {format_size(total_size)}\n\n"
                            f"{DEVELOPER}"
                        )
                    except FloodWait as e:
                        time.sleep(e.x)
                    except:
                        pass
                    
                    start_time = time.time()
    
    return total_size

@app.on_message(filters.command("start"))
async def start(client, message):
    await message.reply(
        f"**Terabox Video Bot**\n\n"
        f"Send me any Terabox link and I'll download/stream it for you!\n\n"
        f"{DEVELOPER}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Help", callback_data="help")]
        ])
    )

@app.on_message(filters.text & ~filters.command("start"))
async def handle_terabox_link(client, message: Message):
    url = message.text.strip()
    if "terabox.app" not in url:
        await message.reply("Please send a valid Terabox link")
        return
    
    try:
        msg = await message.reply("Processing your link...")
        direct_link = get_direct_link(url)
        
        await msg.edit(
            "Choose an option:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📥 Download Video", callback_data=f"download_{direct_link}"),
                    InlineKeyboardButton("▶️ Stream Video", callback_data=f"stream_{url}")
                ]
            ])
        )
    except Exception as e:
        await message.reply(f"Error: {str(e)}")

@app.on_callback_query(filters.regex(r"^download_"))
async def download_video(client, callback_query):
    direct_link = callback_query.data.split("_", 1)[1]
    msg = await callback_query.message.edit("Starting download...")
    
    local_filename = "terabox_video.mp4"
    try:
        file_size = await download_with_progress(client, msg, direct_link, local_filename)
        
        await msg.edit("Uploading to Telegram...")
        await callback_query.message.reply_video(
            video=local_filename,
            caption=f"{CAPTION}\n\n"
                   f"📁 Size: {format_size(file_size)}\n"
                   f"⚡ Powered by {DEVELOPER}",
            progress=progress_callback,
            progress_args=(msg,)
        )
    except Exception as e:
        await msg.edit(f"Download failed: {str(e)}")
    finally:
        if os.path.exists(local_filename):
            os.remove(local_filename)

async def progress_callback(current, total, message):
    progress = (current / total) * 100
    try:
        await message.edit_text(
            f"**Uploading...**\n\n"
            f"▰ {progress:.2f}% Completed\n"
            f"📦 Size: {format_size(current)} / {format_size(total)}\n\n"
            f"{DEVELOPER}"
        )
    except:
        pass

@app.on_callback_query(filters.regex(r"^stream_"))
async def stream_video(client, callback_query):
    terabox_url = callback_query.data.split("_", 1)[1]
    direct_link = get_direct_link(terabox_url)
    
    await callback_query.message.edit(
        f"**Stream Link**\n\n"
        f"🔗 {direct_link}\n\n"
        f"You can play this in any video player that supports direct links\n\n"
        f"{DEVELOPER}\n"
        f"{CAPTION}",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Open Link", url=direct_link)]
        ])
    )

app.run()
