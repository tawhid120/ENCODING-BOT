

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .. import video_mimetype
from ..utils.compression import pending_videos
from ..utils.database.add_user import AddUserToDatabase
from ..utils.helper import check_chat


@Client.on_message(filters.private & (filters.video | filters.document), group=1)
async def on_video_received(app, message):
    """
    When a user sends or forwards a video in private chat,
    show an inline keyboard with resolution options for compression.
    """
    c = await check_chat(message, chat='Both')
    if not c:
        return

    # Skip if message has a command caption (handled by /dl, /af, etc.)
    if message.caption and message.caption.startswith('/'):
        return

    # For documents, only handle video mime types
    if message.document and message.document.mime_type not in video_mimetype:
        return

    await AddUserToDatabase(app, message)

    # Get file info for display
    if message.video:
        file_size = message.video.file_size or 0
        file_name = message.video.file_name or "video"
    elif message.document:
        file_size = message.document.file_size or 0
        file_name = message.document.file_name or "document"
    else:
        return

    size_mb = round(file_size / (1024 * 1024), 2)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📹 360p", callback_data="compress_360p"),
            InlineKeyboardButton("📹 480p", callback_data="compress_480p"),
        ],
        [
            InlineKeyboardButton("📹 720p", callback_data="compress_720p"),
            InlineKeyboardButton("📹 1080p", callback_data="compress_1080p"),
        ],
        [
            InlineKeyboardButton("❌ Cancel", callback_data="closeMeh"),
        ]
    ])

    picker_msg = await message.reply(
        text=f"<b>🎬 Video Compression</b>\n\n"
             f"📁 <b>File:</b> <code>{file_name}</code>\n"
             f"📦 <b>Size:</b> {size_mb} MB\n\n"
             f"Select the target resolution for compression:",
        reply_markup=keyboard,
        quote=True
    )

    # Store reference to the original video message, keyed by the picker message
    pending_videos[f"{message.chat.id}:{picker_msg.id}"] = message
