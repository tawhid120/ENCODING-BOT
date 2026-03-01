

import asyncio
import os
import shutil

from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                            KeyboardButton, Message, ReplyKeyboardMarkup)
from pySmartDL import SmartDL

from .. import download_dir, encode_dir
from .database.access_db import db
from .display_progress import progress_for_url
from .encoding import encode, extract_subs
from .uploads import upload_worker

output = InlineKeyboardMarkup([
    [InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ", url="https://t.me/juktijol"),
     InlineKeyboardButton("JuktiJol", url="https://t.me/juktijol")]
])

start_but = InlineKeyboardMarkup([
    [InlineKeyboardButton("🗜 Compress Guide", callback_data="compress_guide")],
    [InlineKeyboardButton("📖 How to Use", callback_data="how_to_use"),
     InlineKeyboardButton("📋 Commands", callback_data="commands_list")],
    [InlineKeyboardButton("⚙️ Settings", callback_data="OpenSettings"),
     InlineKeyboardButton("📊 Stats", callback_data="stats")],
    [InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/juktijol"),
     InlineKeyboardButton("📢 Channel", url="https://t.me/juktijol")]])

reply_keyboard = ReplyKeyboardMarkup(
    [
        [KeyboardButton("🗜 Compress Guide")],
        [KeyboardButton("📖 Help"), KeyboardButton("⚙️ Settings")],
        [KeyboardButton("📊 Stats"), KeyboardButton("📋 Queue")],
        [KeyboardButton("📹 View Settings"), KeyboardButton("🔄 Reset Settings")],
    ],
    resize_keyboard=True,
    is_persistent=False,
)

COMMAND_GUIDE = {
    "🗜 Compress Guide": (
        "compress",
        "<b>🗜 Video Compression Guide</b>\n\n"
        "<b>📌 What is Compression?</b>\n"
        "Compression reduces your video file size while keeping "
        "acceptable visual quality — perfect for saving storage or "
        "sharing on slow networks.\n\n"
        "<b>📹 How to Compress a Video:</b>\n"
        "1️⃣ Send a video file to this bot\n"
        "2️⃣ Choose a resolution: <b>240p, 480p, 720p, or 1080p</b>\n"
        "3️⃣ Wait for the bot to compress and send it back!\n\n"
        "<b>🎯 Resolution Presets:</b>\n"
        "┌─────────────────────────────┐\n"
        "│ <b>📹 240p</b>  — Max compression     │\n"
        "│ <b>📹 480p</b>  — Balanced quality     │\n"
        "│ <b>📹 720p</b>  — HD quality           │\n"
        "│ <b>📹 1080p</b> — Full HD quality      │\n"
        "└─────────────────────────────┘\n\n"
        "<b>⚙️ Technical Details:</b>\n"
        "• Codec: <b>H.264 (libx264)</b>\n"
        "• Preset: <b>Ultrafast</b> (fast processing)\n"
        "• Audio: <b>AAC Stereo</b>\n"
        "• Format: <b>MP4</b> with fast-start enabled\n\n"
        "<b>💡 Tips:</b>\n"
        "• Lower resolution = smaller file size\n"
        "• 480p is ideal for most mobile viewing\n"
        "• 720p gives a great balance of size & quality\n"
        "• Use /settings for advanced encoding options"
    ),
    "📖 Help": (
        "/help",
        "<b>📖 Help Command Guide</b>\n\n"
        "Shows the full list of available commands with descriptions.\n\n"
        "<b>Usage:</b> Simply tap the <b>📖 Help</b> button or type /help"
    ),
    "⚙️ Settings": (
        "/settings",
        "<b>⚙️ Settings Command Guide</b>\n\n"
        "Opens the encoding settings panel where you can customize:\n"
        "• <b>Video</b> — Codec (H264/H265), resolution, CRF quality, frame rate\n"
        "• <b>Audio</b> — Codec, bitrate, channels, sample rate\n"
        "• <b>Extras</b> — Subtitles, upload mode, watermark, metadata\n\n"
        "<b>Usage:</b> Tap <b>⚙️ Settings</b> or type /settings"
    ),
    "📊 Stats": (
        "/stats",
        "<b>📊 Stats Command Guide</b>\n\n"
        "Displays bot and system statistics including:\n"
        "• Bot & OS uptime\n"
        "• Disk, CPU, RAM usage\n"
        "• Total registered users\n\n"
        "<b>Usage:</b> Tap <b>📊 Stats</b> or type /stats"
    ),
    "📋 Queue": (
        "/queue",
        "<b>📋 Queue Command Guide</b>\n\n"
        "Shows the current encoding queue — check how many files are "
        "waiting to be processed and your position in the queue.\n\n"
        "<b>Usage:</b> Tap <b>📋 Queue</b> or type /queue"
    ),
    "📹 View Settings": (
        "/vset",
        "<b>📹 View Settings Command Guide</b>\n\n"
        "Displays your current encoding settings at a glance, including "
        "video codec, resolution, CRF, audio codec, bitrate, and more.\n\n"
        "<b>Usage:</b> Tap <b>📹 View Settings</b> or type /vset"
    ),
    "🔄 Reset Settings": (
        "/reset",
        "<b>🔄 Reset Settings Command Guide</b>\n\n"
        "Resets all your encoding settings back to default values.\n"
        "Use this if you want a fresh start.\n\n"
        "<b>Usage:</b> Tap <b>🔄 Reset Settings</b> or type /reset"
    ),
}


def get_start_text(mention=None):
    greeting = f"👋 <b>Welcome, {mention}!</b>" if mention else "<b>🏠 Home</b>"
    return (
        f"{greeting}\n\n"
        f"I'm a <b>Video Encoder Bot</b> — I can compress and encode your videos "
        f"with custom quality, codec, and audio settings.\n\n"
        f"<b>Quick Start:</b>\n"
        f"1️⃣ Send me a video file or document\n"
        f"2️⃣ The bot will automatically start encoding\n"
        f"3️⃣ Get your compressed video back!\n\n"
        f"Tap <b>📖 How to Use</b> below for a full guide."
    )


async def check_chat(message, chat):
    ''' Allow all users. '''
    return True


async def handle_url(url, filepath, msg):
    downloader = SmartDL(url, filepath, progress_bar=False, threads=10)
    downloader.start(blocking=False)
    while not downloader.isFinished():
        await progress_for_url(downloader, msg)


async def handle_encode(filepath, message, msg, audio_map=None):
    if await db.get_hardsub(message.from_user.id):
        subs = await extract_subs(filepath, msg, message.from_user.id)
        if not subs:
            await msg.edit("Something went wrong while extracting the subtitles!")
            return
    new_file = await encode(filepath, message, msg, audio_map=audio_map)
    if new_file:
        await msg.edit("<code>Video Encoded, getting metadata...</code>")
        try:
            link = await upload_worker(new_file, message, msg)
            await msg.edit('Video Encoded Successfully! Link: {}'.format(link))
        except Exception as e:
            await msg.edit(f"Error while uploading: {e}")
            link = None

        # Immediate cleanup after upload
        try:
            os.remove(new_file)
            os.remove(filepath)
        except Exception:
            pass

    else:
        await message.reply("<code>Something wents wrong while encoding your file.</code>")
        try:
            os.remove(filepath)
        except Exception:
            pass
        link = None

    return link


async def handle_extract(archieve):
    # get current directory
    path = os.getcwd()
    archieve = os.path.join(path, archieve)
    cmd = [f'./extract', archieve]
    rio = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    await rio.communicate()
    os.remove(archieve)
    return path


async def get_zip_folder(orig_path: str):
    if orig_path.endswith(".tar.bz2"):
        return orig_path.rsplit(".tar.bz2", 1)[0]
    elif orig_path.endswith(".tar.gz"):
        return orig_path.rsplit(".tar.gz", 1)[0]
    elif orig_path.endswith(".bz2"):
        return orig_path.rsplit(".bz2", 1)[0]
    elif orig_path.endswith(".gz"):
        return orig_path.rsplit(".gz", 1)[0]
    elif orig_path.endswith(".tar.xz"):
        return orig_path.rsplit(".tar.xz", 1)[0]
    elif orig_path.endswith(".tar"):
        return orig_path.rsplit(".tar", 1)[0]
    elif orig_path.endswith(".tbz2"):
        return orig_path.rsplit("tbz2", 1)[0]
    elif orig_path.endswith(".tgz"):
        return orig_path.rsplit(".tgz", 1)[0]
    elif orig_path.endswith(".zip"):
        return orig_path.rsplit(".zip", 1)[0]
    elif orig_path.endswith(".7z"):
        return orig_path.rsplit(".7z", 1)[0]
    elif orig_path.endswith(".Z"):
        return orig_path.rsplit(".Z", 1)[0]
    elif orig_path.endswith(".rar"):
        return orig_path.rsplit(".rar", 1)[0]
    elif orig_path.endswith(".iso"):
        return orig_path.rsplit(".iso", 1)[0]
    elif orig_path.endswith(".wim"):
        return orig_path.rsplit(".wim", 1)[0]
    elif orig_path.endswith(".cab"):
        return orig_path.rsplit(".cab", 1)[0]
    elif orig_path.endswith(".apm"):
        return orig_path.rsplit(".apm", 1)[0]
    elif orig_path.endswith(".arj"):
        return orig_path.rsplit(".arj", 1)[0]
    elif orig_path.endswith(".chm"):
        return orig_path.rsplit(".chm", 1)[0]
    elif orig_path.endswith(".cpio"):
        return orig_path.rsplit(".cpio", 1)[0]
    elif orig_path.endswith(".cramfs"):
        return orig_path.rsplit(".cramfs", 1)[0]
    elif orig_path.endswith(".deb"):
        return orig_path.rsplit(".deb", 1)[0]
    elif orig_path.endswith(".dmg"):
        return orig_path.rsplit(".dmg", 1)[0]
    elif orig_path.endswith(".fat"):
        return orig_path.rsplit(".fat", 1)[0]
    elif orig_path.endswith(".hfs"):
        return orig_path.rsplit(".hfs", 1)[0]
    elif orig_path.endswith(".lzh"):
        return orig_path.rsplit(".lzh", 1)[0]
    elif orig_path.endswith(".lzma"):
        return orig_path.rsplit(".lzma", 1)[0]
    elif orig_path.endswith(".lzma2"):
        return orig_path.rsplit(".lzma2", 1)[0]
    elif orig_path.endswith(".mbr"):
        return orig_path.rsplit(".mbr", 1)[0]
    elif orig_path.endswith(".msi"):
        return orig_path.rsplit(".msi", 1)[0]
    elif orig_path.endswith(".mslz"):
        return orig_path.rsplit(".mslz", 1)[0]
    elif orig_path.endswith(".nsis"):
        return orig_path.rsplit(".nsis", 1)[0]
    elif orig_path.endswith(".ntfs"):
        return orig_path.rsplit(".ntfs", 1)[0]
    elif orig_path.endswith(".rpm"):
        return orig_path.rsplit(".rpm", 1)[0]
    elif orig_path.endswith(".squashfs"):
        return orig_path.rsplit(".squashfs", 1)[0]
    elif orig_path.endswith(".udf"):
        return orig_path.rsplit(".udf", 1)[0]
    elif orig_path.endswith(".vhd"):
        return orig_path.rsplit(".vhd", 1)[0]
    elif orig_path.endswith(".xar"):
        return orig_path.rsplit(".xar", 1)[0]
    else:
        raise IndexError("File format not supported for extraction!")


def delete_downloads():
    dir = encode_dir
    dir2 = download_dir
    for files in os.listdir(dir):
        path = os.path.join(dir, files)
        try:
            shutil.rmtree(path)
        except OSError:
            try:
                os.remove(path)
            except PermissionError:
                pass
    for files in os.listdir(dir2):
        path = os.path.join(dir2, files)
        try:
            shutil.rmtree(path)
        except OSError:
            try:
                os.remove(path)
            except PermissionError:
                pass
