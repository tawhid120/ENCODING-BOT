

import os
import time

from ... import app, download_dir, log, LOGGER
from ..database.access_db import db
from ..display_progress import progress_for_pyrogram
from ..encoding import get_duration, get_thumbnail, get_width_height

# Pyrofork uses MTProto protocol which natively supports files up to 2GB
# with a standard Bot Token — no Local API Server or Userbot needed.
MAX_UPLOAD_SIZE = 2 * 1024 * 1024 * 1024  # 2 GB in bytes


async def upload_to_tg(new_file, message, msg):
    # Variables
    c_time = time.time()
    filename = os.path.basename(new_file)
    duration = get_duration(new_file)

    # Check file size against Pyrofork MTProto limit (2GB)
    file_size = os.path.getsize(new_file)
    if file_size > MAX_UPLOAD_SIZE:
        if file_size >= 1024 * 1024 * 1024:
            size_display = f"{round(file_size / (1024 * 1024 * 1024), 2)} GB"
        else:
            size_display = f"{round(file_size / (1024 * 1024), 2)} MB"
        LOGGER.warning(f"File {filename} is {size_display}, exceeds 2GB MTProto limit.")
        await msg.edit(
            f"<b>⚠️ File too large for upload!</b>\n\n"
            f"📦 <b>Size:</b> {size_display}\n"
            f"📏 <b>Limit:</b> 2 GB (Pyrofork MTProto)\n\n"
            f"The compressed file still exceeds the limit. "
            f"Please try encoding with a lower resolution or bitrate."
        )
        return None

    # Thumbnail Logic
    custom_thumb = await db.get_thumbnail(message.from_user.id)
    if custom_thumb:
        thumb = await app.download_media(custom_thumb, file_name=os.path.join(download_dir, str(time.time()) + ".jpg"))
    else:
        thumb = get_thumbnail(new_file, download_dir, duration / 4)

    width, height = get_width_height(new_file)
    # Handle Upload
    if await db.get_upload_as_doc(message.from_user.id) is True:
        link = await upload_doc(message, msg, c_time, filename, new_file)
    else:
        link = await upload_video(message, msg, new_file, filename,
                                  c_time, thumb, duration, width, height)

    # Cleanup custom thumb download if it was used/downloaded
    if custom_thumb and thumb and os.path.isfile(thumb):
        try:
            os.remove(thumb)
        except Exception:
            pass

    return link


async def upload_video(message, msg, new_file, filename, c_time, thumb, duration, width, height):
    resp = await message.reply_video(
        new_file,
        supports_streaming=True,
        parse_mode=None,
        caption=filename,
        thumb=thumb,
        duration=duration,
        width=width,
        height=height,
        progress=progress_for_pyrogram,
        progress_args=("Uploading ...", msg, c_time)
    )
    if resp:
        await app.send_video(log, resp.video.file_id, thumb=thumb,
                             caption=filename, duration=duration,
                             width=width, height=height, parse_mode=None)

    return resp.link


async def upload_doc(message, msg, c_time, filename, new_file):
    resp = await message.reply_document(
        new_file,
        caption=filename,
        progress=progress_for_pyrogram,
        progress_args=("Uploading ...", msg, c_time)
    )

    if resp:
        await app.send_document(log, resp.document.file_id, caption=filename, parse_mode=None)

    return resp.link
