

import datetime
import json
import os

from pyrogram import Client
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from .. import app, data, download_dir, log, LOGGER, video_mimetype
from ..plugins.queue import queue_answer
from ..utils.compression import compress_tasks, pending_videos
from ..utils.database.access_db import db
from ..utils.helper import get_start_text, start_but
from ..utils.settings import (AudioSettings, ExtraSettings, OpenSettings,
                              VideoSettings)
from ..utils.tasks import handle_tasks
from .start import showw_status
from ..video_utils.audio_selector import sessions


@app.on_callback_query()
async def callback_handlers(bot: Client, cb: CallbackQuery):
    try:
        # Close Button

        if cb.data == "closeMeh":
            await cb.message.delete(True)

        # Compression Guide
        elif cb.data == "compress_guide":
            text = (
                "<b>🗜 Video Compression Guide</b>\n\n"
                "<b>📌 What is Compression?</b>\n"
                "Compression reduces your video file size while keeping "
                "acceptable visual quality — perfect for saving storage "
                "or sharing on slow networks.\n\n"
                "<b>📹 How to Compress a Video:</b>\n"
                "1️⃣ Send a video file to this bot\n"
                "2️⃣ Choose a resolution: <b>240p, 480p, 720p, or 1080p</b>\n"
                "3️⃣ Wait for the bot to compress and send it back!\n\n"
                "<b>🎯 Resolution Presets:</b>\n"
                "┌──────────────────────────────────────┐\n"
                "│ <b>📹 240p</b>  — Max compression, tiny size     │\n"
                "│ <b>📹 480p</b>  — Balanced quality & size        │\n"
                "│ <b>📹 720p</b>  — HD quality, moderate size      │\n"
                "│ <b>📹 1080p</b> — Full HD, larger size           │\n"
                "└──────────────────────────────────────┘\n\n"
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
            )
            guide_btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("📹 240p", callback_data="compress_240p"),
                 InlineKeyboardButton("📹 480p", callback_data="compress_480p")],
                [InlineKeyboardButton("📹 720p", callback_data="compress_720p"),
                 InlineKeyboardButton("📹 1080p", callback_data="compress_1080p")],
                [InlineKeyboardButton("⚙️ Settings", callback_data="OpenSettings"),
                 InlineKeyboardButton("📋 Commands", callback_data="commands_list")],
                [InlineKeyboardButton("🔙 Back to Home", callback_data="go_home")]
            ])
            await cb.message.edit(text=text, reply_markup=guide_btn, disable_web_page_preview=True)

        # How to Use Guide
        elif cb.data == "how_to_use":
            text = (
                "<b>📖 How to Use This Bot</b>\n\n"
                "<b>Step 1: Send a Video</b>\n"
                "Send any video file or document directly to this bot. "
                "The bot will automatically detect it and start encoding.\n\n"
                "<b>Step 2: Adjust Settings (Optional)</b>\n"
                "Before sending a video, you can customize:\n"
                "• <b>Video</b> — Codec (H264/H265), resolution, CRF quality\n"
                "• <b>Audio</b> — Codec, bitrate, channels, sample rate\n"
                "• <b>Extras</b> — Subtitles, upload mode, watermark\n"
                "Tap ⚙️ <b>Settings</b> to configure these.\n\n"
                "<b>Step 3: Get Your Encoded Video</b>\n"
                "Once encoding is done, the bot will send the compressed "
                "video back to you.\n\n"
                "<b>Other Features:</b>\n"
                "• /ddl [url] | [name] — Encode from a direct link\n"
                "• /batch [url] — Encode multiple files\n"
                "• /af — Rearrange audio tracks (reply to a video)\n"
                "• /queue — Check your position in the queue"
            )
            back_btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("⚙️ Settings", callback_data="OpenSettings"),
                 InlineKeyboardButton("📋 Commands", callback_data="commands_list")],
                [InlineKeyboardButton("🔙 Back to Home", callback_data="go_home")]
            ])
            await cb.message.edit(text=text, reply_markup=back_btn, disable_web_page_preview=True)

        # Commands List
        elif cb.data == "commands_list":
            text = (
                "<b>📋 Available Commands</b>\n\n"
                "<b>📹 Encoding:</b>\n"
                "• Send a video → Auto encode\n"
                "• /dl — Encode a Telegram video (reply to file)\n"
                "• /ddl [url] | [name] — Encode from direct link\n"
                "• /batch [url] — Batch encode from link\n"
                "• /af — Rearrange audio tracks (reply to file)\n\n"
                "<b>⚙️ Settings:</b>\n"
                "• /settings — Open encoding settings\n"
                "• /vset — View current settings\n"
                "• /reset — Reset to default settings\n\n"
                "<b>📊 Info:</b>\n"
                "• /queue — Check encoding queue\n"
                "• /stats — View bot & system stats\n"
                "• /help — Show all commands"
            )
            back_btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("📖 How to Use", callback_data="how_to_use"),
                 InlineKeyboardButton("⚙️ Settings", callback_data="OpenSettings")],
                [InlineKeyboardButton("🔙 Back to Home", callback_data="go_home")]
            ])
            await cb.message.edit(text=text, reply_markup=back_btn, disable_web_page_preview=True)

        # Back to Home / Start Menu
        elif cb.data == "go_home":
            text = get_start_text()
            await cb.message.edit(text=text, reply_markup=start_but, disable_web_page_preview=True)

        # Settings

        elif cb.data == "VideoSettings":
            await VideoSettings(cb.message, user_id=cb.from_user.id)

        elif cb.data == "OpenSettings":
            await OpenSettings(cb.message, user_id=cb.from_user.id)

        elif cb.data == "AudioSettings":
            await AudioSettings(cb.message, user_id=cb.from_user.id)

        elif cb.data == "ExtraSettings":
            await ExtraSettings(cb.message, user_id=cb.from_user.id)

        elif cb.data == "triggerMode":
            if await db.get_drive(cb.from_user.id) is True:
                await db.set_drive(cb.from_user.id, drive=False)
            else:
                await db.set_drive(cb.from_user.id, drive=True)
            await ExtraSettings(cb.message, user_id=cb.from_user.id)

        elif cb.data == "triggerUploadMode":
            if await db.get_upload_as_doc(cb.from_user.id) is True:
                await db.set_upload_as_doc(cb.from_user.id, upload_as_doc=False)
            else:
                await db.set_upload_as_doc(cb.from_user.id, upload_as_doc=True)
            await ExtraSettings(cb.message, user_id=cb.from_user.id)

        elif cb.data == "triggerResize":
            if await db.get_resize(cb.from_user.id) is True:
                await db.set_resize(cb.from_user.id, resize=False)
            else:
                await db.set_resize(cb.from_user.id, resize=True)
            await ExtraSettings(cb.message, user_id=cb.from_user.id)

        # Watermark
        elif cb.data == "Watermark":
            await cb.answer("Sir, this button not works XD\n\nPress Bottom Buttons.", show_alert=True)

        # Metadata
        elif cb.data == "triggerMetadata":
            if await db.get_metadata_w(cb.from_user.id):
                await db.set_metadata_w(cb.from_user.id, metadata=False)
            else:
                await db.set_metadata_w(cb.from_user.id, metadata=True)
            await ExtraSettings(cb.message, user_id=cb.from_user.id)

        # Watermark
        elif cb.data == "triggerVideo":
            if await db.get_watermark(cb.from_user.id):
                await db.set_watermark(cb.from_user.id, watermark=False)
            else:
                await db.set_watermark(cb.from_user.id, watermark=True)
            await ExtraSettings(cb.message, user_id=cb.from_user.id)

        # Subtitles
        elif cb.data == "triggerHardsub":
            if await db.get_hardsub(cb.from_user.id):
                await db.set_hardsub(cb.from_user.id, hardsub=False)
            else:
                await db.set_hardsub(cb.from_user.id, hardsub=True)
            await ExtraSettings(cb.message, user_id=cb.from_user.id)

        elif cb.data == "triggerSubtitles":
            if await db.get_subtitles(cb.from_user.id):
                await db.set_subtitles(cb.from_user.id, subtitles=False)
            else:
                await db.set_subtitles(cb.from_user.id, subtitles=True)
            await ExtraSettings(cb.message, user_id=cb.from_user.id)

        # Extension
        elif cb.data == "triggerextensions":
            ex = await db.get_extensions(cb.from_user.id)
            if ex == 'MP4':
                await db.set_extensions(cb.from_user.id, extensions='MKV')
            elif ex == 'MKV':
                await db.set_extensions(cb.from_user.id, extensions='AVI')
            else:
                await db.set_extensions(cb.from_user.id, extensions='MP4')
            await VideoSettings(cb.message, user_id=cb.from_user.id)

        # Frame
        elif cb.data == "triggerframe":
            fr = await db.get_frame(cb.from_user.id)
            if fr == 'ntsc':
                await db.set_frame(cb.from_user.id, frame='source')
            elif fr == 'source':
                await db.set_frame(cb.from_user.id, frame='pal')
            elif fr == 'pal':
                await db.set_frame(cb.from_user.id, frame='film')
            elif fr == 'film':
                await db.set_frame(cb.from_user.id, frame='23.976')
            elif fr == '23.976':
                await db.set_frame(cb.from_user.id, frame='30')
            elif fr == '30':
                await db.set_frame(cb.from_user.id, frame='60')
            else:
                await db.set_frame(cb.from_user.id, frame='ntsc')
            await VideoSettings(cb.message, user_id=cb.from_user.id)

        # Preset
        elif cb.data == "triggerPreset":
            p = await db.get_preset(cb.from_user.id)
            if p == 'uf':
                await db.set_preset(cb.from_user.id, preset='sf')
            elif p == 'sf':
                await db.set_preset(cb.from_user.id, preset='vf')
            elif p == 'vf':
                await db.set_preset(cb.from_user.id, preset='f')
            elif p == 'f':
                await db.set_preset(cb.from_user.id, preset='m')
            elif p == 'm':
                await db.set_preset(cb.from_user.id, preset='s')
            else:
                await db.set_preset(cb.from_user.id, preset='uf')
            await VideoSettings(cb.message, user_id=cb.from_user.id)

        # sample rate
        elif cb.data == "triggersamplerate":
            sr = await db.get_samplerate(cb.from_user.id)
            if sr == '44.1K':
                await db.set_samplerate(cb.from_user.id, sample='48K')
            elif sr == '48K':
                await db.set_samplerate(cb.from_user.id, sample='source')
            else:
                await db.set_samplerate(cb.from_user.id, sample='44.1K')
            await AudioSettings(cb.message, user_id=cb.from_user.id)

        # bitrate
        elif cb.data == "triggerbitrate":
            bit = await db.get_bitrate(cb.from_user.id)
            if bit == '400':
                await db.set_bitrate(cb.from_user.id, bitrate='320')
            elif bit == '320':
                await db.set_bitrate(cb.from_user.id, bitrate='256')
            elif bit == '256':
                await db.set_bitrate(cb.from_user.id, bitrate='224')
            elif bit == '224':
                await db.set_bitrate(cb.from_user.id, bitrate='192')
            elif bit == '192':
                await db.set_bitrate(cb.from_user.id, bitrate='160')
            elif bit == '160':
                await db.set_bitrate(cb.from_user.id, bitrate='128')
            elif bit == '128':
                await db.set_bitrate(cb.from_user.id, bitrate='source')
            else:
                await db.set_bitrate(cb.from_user.id, bitrate='400')
            await AudioSettings(cb.message, user_id=cb.from_user.id)

        # Audio Codec
        elif cb.data == "triggerAudioCodec":
            a = await db.get_audio(cb.from_user.id)
            if a == 'dd':
                await db.set_audio(cb.from_user.id, audio='copy')
            elif a == 'copy':
                await db.set_audio(cb.from_user.id, audio='aac')
            elif a == 'aac':
                await db.set_audio(cb.from_user.id, audio='opus')
            elif a == 'opus':
                await db.set_audio(cb.from_user.id, audio='alac')
            elif a == 'alac':
                await db.set_audio(cb.from_user.id, audio='vorbis')
            else:
                await db.set_audio(cb.from_user.id, audio='dd')
            await AudioSettings(cb.message, user_id=cb.from_user.id)

        # Audio Channel
        elif cb.data == "triggerAudioChannels":
            c = await db.get_channels(cb.from_user.id)
            if c == 'source':
                await db.set_channels(cb.from_user.id, channels='1.0')
            elif c == '1.0':
                await db.set_channels(cb.from_user.id, channels='2.0')
            elif c == '2.0':
                await db.set_channels(cb.from_user.id, channels='2.1')
            elif c == '2.1':
                await db.set_channels(cb.from_user.id, channels='5.1')
            elif c == '5.1':
                await cb.answer("7.1 is for bluray only.", show_alert=True)
                await db.set_channels(cb.from_user.id, channels='7.1')
            else:
                await db.set_channels(cb.from_user.id, channels='source')
            await AudioSettings(cb.message, user_id=cb.from_user.id)

        # Resolution
        elif cb.data == "triggerResolution":
            r = await db.get_resolution(cb.from_user.id)
            if r == 'OG':
                await db.set_resolution(cb.from_user.id, resolution='1080')
            elif r == '1080':
                await db.set_resolution(cb.from_user.id, resolution='720')
            elif r == '720':
                await db.set_resolution(cb.from_user.id, resolution='480')
            elif r == '480':
                await db.set_resolution(cb.from_user.id, resolution='240')
            elif r == '240':
                await db.set_resolution(cb.from_user.id, resolution='576')
            else:
                await db.set_resolution(cb.from_user.id, resolution='OG')
            await VideoSettings(cb.message, user_id=cb.from_user.id)

        # Video Bits
        elif cb.data == "triggerBits":
            b = await db.get_bits(cb.from_user.id)
            if await db.get_hevc(cb.from_user.id):
                if b:
                    await db.set_bits(cb.from_user.id, bits=False)
                else:
                    await db.set_bits(cb.from_user.id, bits=True)
            else:
                if b:
                    await db.set_bits(cb.from_user.id, bits=False)
                else:
                    await cb.answer("H264 don't support 10 bits in this bot.",
                                    show_alert=True)
            await VideoSettings(cb.message, user_id=cb.from_user.id)

        # HEVC
        elif cb.data == "triggerHevc":
            if await db.get_hevc(cb.from_user.id):
                await db.set_hevc(cb.from_user.id, hevc=False)
            else:
                await db.set_hevc(cb.from_user.id, hevc=True)
                await cb.answer("H265 need more time for encoding video", show_alert=True)
            await VideoSettings(cb.message, user_id=cb.from_user.id)

        # Tune
        elif cb.data == "triggertune":
            if await db.get_tune(cb.from_user.id):
                await db.set_tune(cb.from_user.id, tune=False)
            else:
                await db.set_tune(cb.from_user.id, tune=True)
            await VideoSettings(cb.message, user_id=cb.from_user.id)

        # Reframe
        elif cb.data == "triggerreframe":
            rf = await db.get_reframe(cb.from_user.id)
            if rf == '4':
                await db.set_reframe(cb.from_user.id, reframe='8')
            elif rf == '8':
                await db.set_reframe(cb.from_user.id, reframe='16')
                await cb.answer("Reframe 16 maybe not support", show_alert=True)
            elif rf == '16':
                await db.set_reframe(cb.from_user.id, reframe='pass')
            else:
                await db.set_reframe(cb.from_user.id, reframe='4')
            await VideoSettings(cb.message, user_id=cb.from_user.id)

        # CABAC
        elif cb.data == "triggercabac":
            if await db.get_cabac(cb.from_user.id):
                await db.set_cabac(cb.from_user.id, cabac=False)
            else:
                await db.set_cabac(cb.from_user.id, cabac=True)
            await VideoSettings(cb.message, user_id=cb.from_user.id)

        # Aspect
        elif cb.data == "triggeraspect":
            if await db.get_aspect(cb.from_user.id):
                await db.set_aspect(cb.from_user.id, aspect=False)
            else:
                await db.set_aspect(cb.from_user.id, aspect=True)
                await cb.answer("This will help to force video to 16:9", show_alert=True)
            await VideoSettings(cb.message, user_id=cb.from_user.id)

        elif cb.data == "triggerCRF":
            crf = await db.get_crf(cb.from_user.id)
            nextcrf = int(crf) + 1
            if nextcrf > 30:
                await db.set_crf(cb.from_user.id, crf=18)
            else:
                await db.set_crf(cb.from_user.id, crf=nextcrf)
            await VideoSettings(cb.message, user_id=cb.from_user.id)

        # Compression Resolution Selection
        elif cb.data.startswith("compress_"):
            resolution = cb.data.replace("compress_", "")  # e.g. "240p"

            # Look up the original video message from pending_videos
            key = f"{cb.message.chat.id}:{cb.message.id}"
            original_msg = pending_videos.pop(key, None)

            if not original_msg:
                await cb.answer("Session expired. Please send the video again.",
                                show_alert=True)
                return

            if not (original_msg.video or
                    (original_msg.document and
                     original_msg.document.mime_type in video_mimetype)):
                await cb.answer("No video found!", show_alert=True)
                return

            # Store compression resolution for this message
            msg_key = f"{original_msg.chat.id}:{original_msg.id}"
            compress_tasks[msg_key] = resolution

            await cb.message.edit(
                f"<b>📥 Queued for compression at {resolution}...</b>")

            # Add to the encoding queue
            data.append(original_msg)
            if len(data) == 1:
                await handle_tasks(original_msg, 'compress')
            else:
                await cb.message.edit("📔 Waiting for queue...")

        # Audio Selector Callbacks
        elif "audiosel" in cb.data:
            user_id = cb.from_user.id
            if user_id in sessions:
                await sessions[user_id].resolve_callback(cb)
            else:
                await cb.answer("Session expired. Please try again.", show_alert=True)

        # Cancel

        elif cb.data == "cancel":
            status = download_dir + "status.json"
            try:
                with open(status, 'r+') as f:
                    statusMsg = json.load(f)
                    user = cb.from_user.id
                    statusMsg['running'] = False
                    f.seek(0)
                    json.dump(statusMsg, f, indent=2)
                    os.remove('VideoEncoder/utils/extras/downloads/process.txt')
                    try:
                        await cb.message.edit_text("🚦🚦 Process Cancelled 🚦🚦")
                        chat_id = log
                        utc_now = datetime.datetime.utcnow()
                        ist_now = utc_now + \
                            datetime.timedelta(minutes=30, hours=5)
                        ist = ist_now.strftime("%d/%m/%Y, %H:%M:%S")
                        bst_now = utc_now + \
                            datetime.timedelta(minutes=00, hours=6)
                        bst = bst_now.strftime("%d/%m/%Y, %H:%M:%S")
                        now = f"\n{ist} (GMT+05:30)`\n`{bst} (GMT+06:00)"
                        await bot.send_message(chat_id, f"**Last Process Cancelled, Bot is Free Now !!** \n\nProcess Done at `{now}`", parse_mode="markdown")
                    except:
                        pass
            except FileNotFoundError:
                 await cb.answer("Nothing to cancel or process already finished!", show_alert=True)

        # Stats
        elif 'stats' in cb.data:
            stats = await showw_status(bot)
            stats = stats.replace('<b>', '')
            stats = stats.replace('</b>', '')
            await cb.answer(stats, show_alert=True)

        # Queue
        elif "queue+" in cb.data:
            await queue_answer(app, cb)
    except Exception as e:
        LOGGER.error(f"Error in callback_handlers: {e}")
        try:
            await cb.answer("An error occurred. Please try again later.", show_alert=True)
        except:
            pass
