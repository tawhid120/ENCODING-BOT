

import asyncio
import json
import math
import os
import re
import time

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from .. import LOGGER, download_dir, encode_dir
from .display_progress import TimeFormatter
from .encoding import media_info

# Shared state for compression tasks
# Maps "chat_id:message_id" -> resolution string (e.g. "480p")
compress_tasks = {}

# Maps "chat_id:picker_message_id" -> original video Message object
pending_videos = {}

# Resolution presets: resolution -> (scale_height, video_bitrate, audio_bitrate, crf)
# Optimized for heavy compression while maintaining acceptable visual quality.
COMPRESS_PRESETS = {
    '240p':  (240,  '300k',  '64k',  30),
    '480p':  (480,  '800k',  '96k',  28),
    '720p':  (720,  '1500k', '128k', 26),
    '1080p': (1080, '2500k', '128k', 24),
}


async def compress_video(filepath, resolution, message, msg):
    """
    Heavy compression using FFmpeg with resolution-specific optimized settings.

    FFmpeg strategy optimized for low RAM (Render free tier, 512MB):
    - libx264 codec with 'ultrafast' preset to minimize memory usage
    - Single thread (-threads 1) to keep peak RAM low
    - CRF (Constant Rate Factor) tuned per resolution
    - maxrate cap prevents bitrate spikes
    - bufsize = 2x maxrate for VBV buffering
    - scale=-2:height maintains aspect ratio with even dimensions
    - AAC audio at reduced bitrate
    - movflags +faststart enables progressive download / streaming
    """
    preset = COMPRESS_PRESETS.get(resolution)
    if not preset:
        LOGGER.error(f"Unknown resolution preset: {resolution}")
        return None

    height, v_bitrate, a_bitrate, crf = preset

    path, extension = os.path.splitext(filepath)
    name = os.path.basename(path)
    output_filepath = os.path.join(encode_dir, name + '_compressed.mp4')

    progress = os.path.join(download_dir, "process.txt")
    with open(progress, 'w') as f:
        pass  # Truncate the progress file for fresh FFmpeg output

    assert output_filepath != filepath

    if os.path.isfile(output_filepath):
        LOGGER.warning(f'"{output_filepath}": file already exists')

    # Calculate bufsize as 2x the video bitrate number
    v_bitrate_num = int(v_bitrate.replace('k', ''))
    bufsize = f'{v_bitrate_num * 2}k'

    command = [
        'ffmpeg', '-hide_banner', '-loglevel', 'error',
        '-progress', progress, '-hwaccel', 'auto',
        '-y', '-i', filepath,
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', str(crf),
        '-maxrate', v_bitrate,
        '-bufsize', bufsize,
        '-vf', f'scale=-2:{height}',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', a_bitrate,
        '-ac', '2',
        '-map', '0:v:0',
        '-map', '0:a?',
        '-movflags', '+faststart',
        '-threads', '1',
        output_filepath
    ]

    proc = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # Progress tracking
    await _handle_compress_progress(proc, msg, message, filepath)

    stdout, stderr = await proc.communicate()
    e_response = stderr.decode().strip()
    if e_response:
        LOGGER.error(f"FFmpeg compression stderr: {e_response}")

    if not os.path.isfile(output_filepath) or os.path.getsize(output_filepath) == 0:
        LOGGER.error(f"Compression failed: {output_filepath} not created or is 0 bytes.")
        if os.path.isfile(output_filepath):
            os.remove(output_filepath)
        return None

    return output_filepath


async def _handle_compress_progress(proc, msg, message, filepath):
    """Track compression progress and update the Telegram message."""
    COMPRESSION_START_TIME = time.time()
    LOGGER.info(f"Compression process PID: {proc.pid}")

    status = os.path.join(download_dir, "status.json")
    with open(status, 'w') as f:
        statusMsg = {
            'running': True,
            'pid': proc.pid,
            'message': msg.id,
            'user': message.from_user.id
        }
        json.dump(statusMsg, f, indent=2)

    while proc.returncode is None:
        await asyncio.sleep(5)
        try:
            with open(os.path.join(download_dir, 'process.txt'), 'r') as file:
                text = file.read()
                time_in_us = re.findall(r"out_time_ms=(\d+)", text)
                progress_status = re.findall(r"progress=(\w+)", text)
                speed = re.findall(r"speed=(\d+\.?\d*)", text)

                if progress_status and progress_status[-1] == "end":
                    break

                if not time_in_us:
                    continue

                elapsed_time = int(time_in_us[-1]) / 1000000
                speed_val = float(speed[-1]) if speed else 1.0
                total_time, _ = await media_info(filepath)

                if not total_time or total_time == 0:
                    continue

                percentage = min(math.floor(elapsed_time * 100 / total_time), 100)
                # Clamp speed to avoid division by zero
                difference = math.floor(
                    (total_time - elapsed_time) / max(speed_val, 0.01))
                ETA = TimeFormatter(difference) if difference > 0 else "-"

                progress_str = "<b>🗜 Compressing Video:</b> {0}%\n{1}{2}".format(
                    round(percentage, 2),
                    ''.join(['█' for _ in range(
                        math.floor(percentage / 10))]),
                    ''.join(['░' for _ in range(
                        10 - math.floor(percentage / 10))])
                )
                stats = f'{progress_str}\n• ETA: {ETA}'

                await msg.edit(
                    text=stats,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton('Cancel', callback_data='cancel'),
                         InlineKeyboardButton('Stats', callback_data='stats')]
                    ])
                )
        except Exception:
            pass
