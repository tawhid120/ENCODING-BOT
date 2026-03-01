

import os
import shutil
import time
from os import execl as osexecl
from subprocess import run as srun
from sys import executable
from time import time

from psutil import (boot_time, cpu_count, cpu_percent, disk_usage,
                    net_io_counters, swap_memory, virtual_memory)
from pyrogram import Client, filters
from pyrogram.types import Message

from .. import botStartTime, download_dir, encode_dir
from ..utils.database.access_db import db
from ..utils.database.add_user import AddUserToDatabase
from ..utils.display_progress import TimeFormatter, humanbytes
from ..utils.helper import check_chat, delete_downloads, start_but

SIZE_UNITS = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']


def uptime():
    """ returns uptime """
    return TimeFormatter(time.time() - botStartTime)


@Client.on_message(filters.command('start'))
async def start_message(app, message):
    c = await check_chat(message, chat='Both')
    if not c:
        return
    await AddUserToDatabase(app, message)
    text = (
        f"👋 <b>Welcome, {message.from_user.mention()}!</b>\n\n"
        f"I'm a <b>Video Encoder Bot</b> — I can compress and encode your videos "
        f"with custom quality, codec, and audio settings.\n\n"
        f"<b>Quick Start:</b>\n"
        f"1️⃣ Send me a video file or document\n"
        f"2️⃣ The bot will automatically start encoding\n"
        f"3️⃣ Get your compressed video back!\n\n"
        f"Tap <b>📖 How to Use</b> below for a full guide."
    )
    await message.reply(text=text, reply_markup=start_but)


@Client.on_message(filters.command('help'))
async def help_message(app, message):
    c = await check_chat(message, chat='Both')
    if not c:
        return
    await AddUserToDatabase(app, message)
    msg = """<b>📕 Commands List</b>

<b>📹 Encoding Commands:</b>
• Send a video file → auto encode
• /dl - Encode a Telegram video (reply to file)
• /ddl - Encode from a direct download link
• /batch - Encode multiple files from a link
• /af - Rearrange audio tracks (reply to file)

<b>⚙️ Settings Commands:</b>
• /settings - Open encoding settings
• /vset - View your current settings
• /reset - Reset all settings to default

<b>📊 Info Commands:</b>
• /queue - Check encoding queue
• /stats - View bot & system stats

<b>👑 Sudo Commands:</b>
• /exec - Execute Python code
• /sh - Execute Shell command
• /vupload - Upload as video
• /dupload - Upload as document
• /gupload - Upload to Google Drive
• /update - Update bot from git
• /restart - Restart the bot
• /clean - Clean temporary files
• /clear - Clear encoding queue
• /logs - View bot logs

<b>👤 Owner Commands:</b>
• /addchat & /addsudo - Add chat/sudo user
• /rmsudo & /rmchat - Remove sudo/chat"""
    await message.reply(text=msg, disable_web_page_preview=True, reply_markup=start_but)


@Client.on_message(filters.command('stats'))
async def show_status_count(_, event: Message):
    c = await check_chat(event, chat='Both')
    if not c:
        return
    await AddUserToDatabase(_, event)
    text = await show_status(_)
    await event.reply_text(text)


async def show_status(_):
    currentTime = TimeFormatter(time() - botStartTime)
    osUptime = TimeFormatter(time() - boot_time())
    total, used, free, disk = disk_usage('/')
    total = humanbytes(total)
    used = humanbytes(used)
    free = humanbytes(free)
    sent = humanbytes(net_io_counters().bytes_sent)
    recv = humanbytes(net_io_counters().bytes_recv)
    cpuUsage = cpu_percent(interval=0.5)
    p_core = cpu_count(logical=False)
    t_core = cpu_count(logical=True)
    swap = swap_memory()
    swap_p = swap.percent
    memory = virtual_memory()
    mem_t = humanbytes(memory.total)
    mem_a = humanbytes(memory.available)
    mem_u = humanbytes(memory.used)
    total_users = await db.total_users_count()
    text = f"""<b>Uptime of</b>:
- <b>Bot:</b> {currentTime}
- <b>OS:</b> {osUptime}

<b>Disk</b>:
<b>- Total:</b> {total}
<b>- Used:</b> {used}
<b>- Free:</b> {free}

<b>UL:</b> {sent} | <b>DL:</b> {recv}
<b>CPU:</b> {cpuUsage}%

<b>Cores:</b>
<b>- Physical:</b> {p_core}
<b>- Total:</b> {t_core}
<b>- Used:</b> {swap_p}%

<b>RAM:</b> 
- <b>Total:</b> {mem_t}
- <b>Free:</b> {mem_a}
- <b>Used:</b> {mem_u}

Users: {total_users}"""
    return text


async def showw_status(_):
    currentTime = TimeFormatter(time() - botStartTime)
    total, used, free, disk = disk_usage('/')
    total = humanbytes(total)
    used = humanbytes(used)
    free = humanbytes(free)
    cpuUsage = cpu_percent(interval=0.5)
    total_users = await db.total_users_count()

    text = f"""Uptime of Bot: {currentTime}

Disk:
- Total: {total}
- Used: {used}
- Free: {free}
CPU: {cpuUsage}%

Users: {total_users}"""
    return text


@Client.on_message(filters.command('clean'))
async def delete_files(_, message):
    c = await check_chat(message, chat='Sudo')
    if not c:
        return
    delete_downloads()
    await message.reply_text('Deleted all junk files!')


@Client.on_message(filters.command('restart'))
async def font_message(app, message):
    c = await check_chat(message, chat='Sudo')
    if not c:
        return
    await AddUserToDatabase(app, message)
    reply = await message.reply_text('Restarting...')
    textx = f"Done Restart...✅"
    await reply.edit_text(textx)
    try:
        exit()
    finally:
        osexecl(executable, executable, "-m", "VideoEncoder")


@Client.on_message(filters.command('update'))
async def update_message(app, message):
    c = await check_chat(message, chat='Sudo')
    if not c:
        return
    await AddUserToDatabase(app, message)
    reply = await message.reply_text('📶 Fetching Update...')
    textx = f"✅ Bot Updated"
    await reply.edit_text(textx)
    try:
        await app.stop()
    finally:
        srun([f"bash run.sh"], shell=True)
