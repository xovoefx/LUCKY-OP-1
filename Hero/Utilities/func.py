from os import path
import asyncio
import os
import shutil
from asyncio import QueueEmpty

from pyrogram.types import InlineKeyboardMarkup
from pyrogram.types.messages_and_media import message

from pyrogram import filters
from pyrogram.types import (InlineKeyboardMarkup, InputMediaPhoto, Message,
                            Voice)
from youtube_search import YoutubeSearch

import Hero
from Hero import (BOT_USERNAME, DURATION_LIMIT, DURATION_LIMIT_MIN,
                   MUSIC_BOT_NAME, app, db_mem)
from Hero.Core.PyTgCalls.Converter import convert
from Hero.Core.PyTgCalls.Downloader import download
from Hero.Core.PyTgCalls.Tgdownloader import telegram_download
from Hero.Database import (get_active_video_chats, get_video_limit,
                            is_active_video_chat)
from Hero.Decorators.assistant import AssistantAdd
from Hero.Decorators.checker import checker
from Hero.Decorators.logger import logging
from Hero.Inline import (livestream_markup, playlist_markup, search_markup,
                          search_markup2, url_markup, url_markup2)
from Hero.Utilities.changers import seconds_to_min, time_to_seconds
from Hero.Utilities.chat import specialfont_to_normal
from Hero.Utilities.stream import start_stream, start_stream_audio
from Hero.Utilities.theme import check_theme
from Hero.Utilities.thumbnails import gen_thumb
from Hero.Utilities.url import get_url
from Hero.Utilities.videostream import start_stream_video
from Hero.Utilities.youtube import (get_yt_info_id, get_yt_info_query,
                                     get_yt_info_query_slider)
from Hero.Utilities.youtube import get_m3u8
from config import get_queue
from Hero import BOT_USERNAME, db_mem
from Hero.Core.PyTgCalls import Queues
from Hero.Core.PyTgCalls.Hero import (join_live_stream, join_video_stream,
                                        stop_stream)
from Hero.Database import (add_active_chat, add_active_video_chat,
                            is_active_chat, music_off, music_on,
                            remove_active_chat)
from Hero.Inline import (audio_markup, audio_markup2, primary_markup,
                          secondary_markup, secondary_markup2)
from Hero.Utilities.timer import start_timer
from Hero.Core.PyTgCalls.Hero import join_stream
from Hero.Database import (add_active_chat, add_active_video_chat,
                            is_active_chat, music_off, music_on)
from Hero.Inline import (audio_markup, audio_markup2, primary_markup,
                          secondary_markup)
from Hero.Utilities.timer import start_timer

loop = asyncio.get_event_loop()

async def mplay_stream(message,MusicData):
    if message.chat.id not in db_mem:
        db_mem[message.chat.id] = {}
    try:
        read1 = db_mem[message.chat.id]["live_check"]
        if read1:
            return await message.reply_text("ʟɪᴠᴇ sᴛʀᴇᴀᴍɪɴɢ ᴘʟᴀʏɪɴɢ.../nsᴛᴏᴘ ɪᴛ ᴛᴏ ᴘʟᴀʏ ᴍᴜsɪᴄ...")
        else:
            pass
    except:
        pass
    callback_data = MusicData.strip()
    callback_request = callback_data.split(None, 1)[1]
    chat_id = message.chat.id
    chat_title = message.chat.title
    videoid, duration, user_id = callback_request.split("|")
    if str(duration) == "None":
        buttons = livestream_markup("720", videoid, duration, user_id)
        return await message.reply_text(
            "**ʟɪᴠᴇ sᴛʀᴇᴀᴍ ᴅᴇᴛᴇᴄᴛᴇᴅ**\n\nᴡᴀɴᴛ ᴛᴏ ᴘʟᴀʏ ʟɪᴠᴇ sᴛʀᴇᴀᴍ? ᴛʜɪs ᴡɪʟʟ sᴛᴏᴘ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴘʟᴀʏɪɴɢ ᴍᴜsɪᴄ ᴀɴᴅ ᴡɪʟʟ sᴛᴀʀᴛ sᴛʀᴇᴀᴍɪɴɢ ʟɪᴠᴇ ᴠɪᴅᴇᴏ...",
            reply_markup=InlineKeyboardMarkup(buttons),
        )    
    await message.delete()
    title, duration_min, duration_sec, thumbnail = get_yt_info_id(videoid)
    if duration_sec > DURATION_LIMIT:
        return await message.reply_text(
            f"**ᴅᴜʀᴀᴛɪᴏɴ ʟɪᴍɪᴛ ᴇxᴄᴇᴇᴅᴇᴅ**\n\n**ᴀʟʟᴏᴡᴇᴅ ᴅᴜʀᴀᴛɪᴏɴ: **{DURATION_LIMIT_MIN} ᴍɪɴᴜᴛᴇs\n**ʀᴇᴄᴇɪᴠᴇᴅ ᴅᴜʀᴀᴛɪᴏɴ:** {duration_min} ᴍɪɴᴜᴛᴇs"
        )
    mystic = await message.reply_text(f"🔄 ᴘʀᴏᴄᴇssɪɴɢ:- {title[:20]}")
    await mystic.edit(
        f"**{MUSIC_BOT_NAME} ᴅᴏᴡɴʟᴏᴀᴅᴇʀ**\n**Title:** {title[:50]}\n\n0% ▓▓▓▓▓▓▓▓▓▓▓▓ 100%"
    )
    downloaded_file = await loop.run_in_executor(
        None, download, videoid, mystic, title
    )
    raw_path = await convert(downloaded_file)
    theme = await check_theme(chat_id)
    chat_title = await specialfont_to_normal(chat_title)
    thumb = await gen_thumb(thumbnail, title, user_id, theme, chat_title)
    if chat_id not in db_mem:
        db_mem[chat_id] = {}
    await custom_start_stream(
        message,
        raw_path,
        videoid,
        thumb,
        title,
        duration_min,
        duration_sec,
        mystic,
    )


async def custom_start_stream(
    message,
    file,
    videoid,
    thumb,
    title,
    duration_min,
    duration_sec,
    mystic,
):
    global get_queue
    if message.chat.id not in db_mem:
        db_mem[message.chat.id] = {}
    wtfbro = db_mem[message.chat.id]
    wtfbro["live_check"] = False
    if await is_active_chat(message.chat.id):
        position = await Queues.put(message.chat.id, file=file)
        _path_ = (
            (str(file))
            .replace("_", "", 1)
            .replace("/", "", 1)
            .replace(".", "", 1)
        )
        buttons = secondary_markup(videoid, message.from_user.id)
        if file not in db_mem:
            db_mem[file] = {}
        cpl = f"cache/{_path_}final.png"
        shutil.copyfile(thumb, cpl)
        wtfbro = db_mem[file]
        wtfbro["title"] = title
        wtfbro["duration"] = duration_min
        wtfbro["username"] = message.from_user.mention
        wtfbro["videoid"] = videoid
        got_queue = get_queue.get(message.chat.id)
        title = title
        user = message.from_user.first_name
        duration = duration_min
        to_append = [title, user, duration]
        got_queue.append(to_append)
        final_output = await message.reply_photo(
            photo=thumb,
            caption=(
                f"🦋<b>__sᴏɴɢ:__ </b>[{title[:25]}](https://www.youtube.com/watch?v={videoid}) \n⏳<b>__ᴅᴜʀᴀᴛɪᴏɴ:__</b> {duration_min} \n👤<b>__ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ:__ </b>{message.from_user.mention} \n🚧<b>__ǫᴜᴇᴜᴇᴅ ᴀᴛ:__</b> <b>#{position}</b>"
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )
        await mystic.delete()        
        os.remove(thumb)
        return
    else:
        if not await join_stream(message.chat.id, file):
            return await mystic.edit("ᴇʀʀᴏʀ ᴊᴏɪɴɪɴɢ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ...")
        get_queue[message.chat.id] = []
        got_queue = get_queue.get(message.chat.id)
        title = title
        user = message.from_user.first_name
        duration = duration_min
        to_append = [title, user, duration]
        got_queue.append(to_append)
        await music_on(message.chat.id)
        await add_active_chat(message.chat.id)
        buttons = primary_markup(
            videoid, message.from_user.id, duration_min, duration_min
        )
        await mystic.delete()
        cap = f"🦋<b>__ᴘʟᴀʏɪɴɢ:__ </b>[{title[:25]}](https://www.youtube.com/watch?v={videoid}) \n👤**__ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ:__** {message.from_user.mention}"
        final_output = await message.reply_photo(
            photo=thumb,
            reply_markup=InlineKeyboardMarkup(buttons),
            caption=cap,
        )
        os.remove(thumb)        
        await start_timer(
            videoid,
            duration_min,
            duration_sec,
            final_output,
            message.chat.id,
            message.from_user.id,
            0,
        )


async def vplay_stream(message,VideoData,mystic):
    limit = await get_video_limit(141414)
    if not limit:
        await message.delete()
        return await message.reply_text(
            "**ɴᴏ ʟɪᴍɪᴛ ᴅᴇғɪɴᴇᴅ ғᴏʀ ᴠɪᴅᴇᴏ ᴄᴀʟʟs**\n\nsᴇᴛ ᴀ ʟɪᴍɪᴛ ғᴏʀ ɴᴜᴍʙᴇʀ ᴏғ ᴍᴀxɪᴍᴜᴍ ᴠɪᴅᴇᴏ ᴄᴀʟʟs ᴀʟʟᴏᴡᴇᴅ ᴏɴ ʙᴏᴛ ʙʏ `/set_video_limit` [sᴜᴅᴏ ᴜsᴇʀs ᴏɴʟʏ]"
        )
    count = len(await get_active_video_chats())
    if int(count) == int(limit):
        if await is_active_video_chat(message.chat.id):
            pass
        else:
            return await message.reply_text("sᴏʀʀʏ ʙᴏᴛ ᴏɴʟʏ ᴀʟʟᴏᴡs ʟɪᴍɪᴛᴇᴅ ɴᴜᴍʙᴇʀ ᴏғ ᴠɪᴅᴇᴏ ᴄᴀʟʟs ᴅᴜᴇ ᴛᴏ ᴄᴘᴜ ᴏᴠᴇʀʟᴏᴀᴅ ɪssᴜᴇs. ᴏᴛʜᴇʀ ᴄʜᴀᴛs ᴀʀᴇ ᴜsɪɴɢ ᴠɪᴅᴇᴏ ᴄᴀʟʟ ʀɪɢʜᴛ ɴᴏᴡ. ᴛʀʏ sᴡɪᴛᴄʜɪɴɢ ᴛᴏ ᴀᴜᴅɪᴏ ᴏʀ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ...")
    if message.chat.id not in db_mem:
        db_mem[message.chat.id] = {}
    try:
        read1 = db_mem[message.chat.id]["live_check"]
        if read1:
            return await message.reply_text("ʟɪᴠᴇ sᴛʀᴇᴀᴍɪɴɢ.../nsᴛᴏᴘ ɪᴛ ᴛᴏ ᴘʟᴀʏ ᴍᴜsɪᴄ...")
        else:
            pass
    except:
        pass    
    callback_data = VideoData.strip()
    callback_request = callback_data.split(None, 1)[1]
    videoid, duration, user_id = callback_request.split("|")    
    
    QualityData = f"ᴠɪᴅᴇᴏsᴛʀᴇᴀᴍ 𝟹𝟼𝟶|{videoid}|{duration}|{user_id}"

    callback_data = QualityData.strip()
    callback_request = callback_data.split(None, 1)[1]
    chat_id = message.chat.id
    chat_title = message.chat.title
    quality, videoid, duration, user_id = callback_request.split("|")
    
    if str(duration) == "None":
        buttons = livestream_markup(quality, videoid, duration, user_id)
        return await message.reply_text(
            "**ʟɪᴠᴇ sᴛʀᴇᴀᴍ ᴅᴇᴛᴇᴄᴛᴇᴅ**\n\nᴡᴀɴᴛ ᴛᴏ ᴘʟᴀʏ ʟɪᴠᴇ sᴛʀᴇᴀᴍ, ᴛʜɪs ᴡɪʟʟ sᴛᴏᴘ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴘʟᴀʏɪɴɢ ᴍᴜsɪᴄ ᴀɴᴅ ᴡɪʟʟ sᴛᴀʀᴛ sᴛʀᴇᴀᴍɪɴɢ ʟɪᴠᴇ ᴠɪᴅᴇᴏ...",
            reply_markup=InlineKeyboardMarkup(buttons),
        )    
    title, duration_min, duration_sec, thumbnail = get_yt_info_id(videoid)
    if duration_sec > DURATION_LIMIT:
        return await message.reply_text(
            f"**ᴅᴜʀᴀᴛɪᴏɴ ʟɪᴍɪᴛ ᴇxᴄᴇᴇᴅᴇᴅ**\n\n**ᴀʟʟᴏᴡᴇᴅ ᴅᴜʀᴀᴛɪᴏɴ: **{DURATION_LIMIT_MIN} ᴍɪɴᴜᴛᴇs\n**ʀᴇᴄᴇɪᴠᴇᴅ ᴅᴜʀᴀᴛɪᴏɴ:** {duration_min} ᴍɪɴᴜᴛᴇs"
        )    
    theme = await check_theme(chat_id)
    chat_title = await specialfont_to_normal(chat_title)
    thumb = await gen_thumb(thumbnail, title, user_id, theme, chat_title)
    nrs, ytlink = await get_m3u8(videoid)
    if nrs == 0:
        return await message.reply_text(
            "ᴠɪᴅᴇᴏ ғᴏʀᴍᴀᴛs ɴᴏᴛ ғᴏᴜɴᴅ..."
        )
    await custom_video_stream(
        message,
        quality,
        ytlink,
        thumb,
        title,
        duration_min,
        duration_sec,
        videoid,
        mystic
    )

async def custom_video_stream(
    message,
    quality,
    link,
    thumb,
    title,
    duration_min,
    duration_sec,
    videoid,
    mystic
):
    global get_queue
    if message.chat.id not in db_mem:
        db_mem[message.chat.id] = {}
    wtfbro = db_mem[message.chat.id]
    wtfbro["live_check"] = False
    if await is_active_chat(message.chat.id):
        file = f"s1s_{quality}_+_{videoid}"
        position = await Queues.put(message.chat.id, file=file)
        _path_ = (
            (str(file))
            .replace("_", "", 1)
            .replace("/", "", 1)
            .replace(".", "", 1)
        )
        buttons = secondary_markup(videoid, message.from_user.id)
        if file not in db_mem:
            db_mem[file] = {}
        cpl = f"cache/{_path_}final.png"
        shutil.copyfile(thumb, cpl)
        wtfbro = db_mem[file]
        wtfbro["chat_title"] = message.chat.title
        wtfbro["duration"] = duration_min
        wtfbro["username"] = message.from_user.mention
        wtfbro["videoid"] = videoid
        wtfbro["user_id"] = message.from_user.id
        got_queue = get_queue.get(message.chat.id)
        title = title
        user = message.from_user.first_name
        duration = duration_min
        to_append = [title, user, duration]
        got_queue.append(to_append)
        final_output = await message.reply_photo(
            photo=thumb,
            caption=(
                f"🦋<b>ᴠɪᴅᴇᴏ:__ </b>[{title[:25]}](https://www.youtube.com/watch?v={videoid}) \n⏳<b>__ᴅᴜʀᴀᴛɪᴏɴ:__</b> {duration_min} \n👤<b>__ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ:__ </b>{message.from_user.mention} \n🚧<b>__ᴠɪᴅᴇᴏ ǫᴜᴇᴜᴇᴅ ᴀᴛ:__</b> <b>#{position}!</b>"
            ),
            reply_markup=InlineKeyboardMarkup(buttons),
        )        
        os.remove(thumb)
        return
    else:
        if not await join_video_stream(
            message.chat.id, link, quality
        ):
            return await message.reply_text(
                f"ᴇʀʀᴏʀ ᴊᴏɪɴɪɴɢ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ..."
            )
        get_queue[message.chat.id] = []
        got_queue = get_queue.get(message.chat.id)
        title = title
        user = message.from_user.first_name
        duration = duration_min
        to_append = [title, user, duration]
        got_queue.append(to_append)
        await music_on(message.chat.id)
        await add_active_video_chat(message.chat.id)
        await add_active_chat(message.chat.id)

        buttons = primary_markup(
            videoid, message.from_user.id, duration_min, duration_min
        )
        cap = f"**ᴠɪᴅᴇᴏ sᴛʀᴇᴀᴍɪɴɢ**\n\n🦋<b>__ᴘʟᴀʏɪɴɢ:__ </b>[{title[:25]}](https://www.youtube.com/watch?v={videoid}) \n👤**__ʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ:__** {message.from_user.mention}"
        final_output = await message.reply_photo(
            photo=thumb,
            reply_markup=InlineKeyboardMarkup(buttons),
            caption=cap,
        )
        os.remove(thumb)        
        await start_timer(
            videoid,
            duration_min,
            duration_sec,
            final_output,
            message.chat.id,
            message.from_user.id,
            0,
        )
        await mystic.delete()
