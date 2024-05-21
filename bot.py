import logging
from pyrogram import Client, filters
from config import Config
import asyncio
import subprocess
import time
import math
import uuid
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Client('bot_session', api_id=Config.TELEGRAM_API_ID, api_hash=Config.TELEGRAM_API_HASH, bot_token=Config.TELEGRAM_BOT_TOKEN)

# Dictionary to store links with unique IDs
link_store = {}

async def progress_for_pyrogram(current, total, message, start_time):
    try:
        now = time.time()
        diff = now - start_time
        if round(diff % 10.00) == 0 or current == total:
            percentage = current * 100 / total
            speed = current / diff
            elapsed_time = round(diff)
            time_to_completion = round((total - current) / speed)
            estimated_total_time = elapsed_time + time_to_completion
            elapsed_time_str = TimeFormatter(elapsed_time)
            estimated_total_time_str = TimeFormatter(estimated_total_time)
            progress = "[{0}{1}]".format(
                ''.join(["⬢" for _ in range(math.floor(percentage / 10))]),
                ''.join(["⬡" for _ in range(10 - math.floor(percentage / 10))])
            )
            progress_message = f"Ripping in progress...\n\n" \
                               f"{progress} {percentage:.2f}%\n" \
                               f"Speed: {humanbytes(speed)}/s\n" \
                               f"ETA: {estimated_total_time_str}"
            await message.edit_text(progress_message)
    except Exception as e:
        logger.error(f'Error in progress_for_pyrogram: {e}')

async def execute_crunchy_command(crunchyroll_link, message, language_option):
    try:
        command = ['./crunchy-cli-v3.6.3-linux-x86_64',
                   '--anonymous', 'archive', '-r', '1280x720', '-a', language_option,
                   crunchyroll_link]
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        start_time = time.time()
        progress_message = await message.reply("Ripping in progress...")

        while True:
            data = await process.stdout.read(1024)
            if not data:
                break
            await progress_for_pyrogram(process.stdout.tell(), 1000, progress_message, start_time)

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return stdout
        else:
            logger.error(f'Error executing command: {stderr.decode()}')
            return None
    except Exception as e:
        logger.exception(f'Error executing command: {str(e)}')
        return None

@app.on_message(filters.command("rip"))
async def handle_rip_command(client, message):
    try:
        crunchyroll_link = message.text.split('/rip', 1)[1].strip()
        logger.info(f'Received rip command for {crunchyroll_link}')

        # Generate a unique ID for the link and store it
        unique_id = str(uuid.uuid4())
        link_store[unique_id] = crunchyroll_link

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Arabic (ME)", callback_data=f"ar-ME|{unique_id}"),
             InlineKeyboardButton("Arabic (SA)", callback_data=f"ar-SA|{unique_id}"),
             InlineKeyboardButton("Catalan", callback_data=f"ca-ES|{unique_id}")],
            [InlineKeyboardButton("German", callback_data=f"de-DE|{unique_id}"),
             InlineKeyboardButton("English (IN)", callback_data=f"en-IN|{unique_id}"),
             InlineKeyboardButton("English (US)", callback_data=f"en-US|{unique_id}")],
            [InlineKeyboardButton("Spanish (419)", callback_data=f"es-419|{unique_id}"),
             InlineKeyboardButton("Spanish (ES)", callback_data=f"es-ES|{unique_id}"),
             InlineKeyboardButton("Spanish (LA)", callback_data=f"es-LA|{unique_id}")],
            [InlineKeyboardButton("French", callback_data=f"fr-FR|{unique_id}"),
             InlineKeyboardButton("Hindi (IN)", callback_data=f"hi-IN|{unique_id}"),
             InlineKeyboardButton("Indonesian", callback_data=f"id-ID|{unique_id}")],
            [InlineKeyboardButton("Italian", callback_data=f"it-IT|{unique_id}"),
             InlineKeyboardButton("Japanese", callback_data=f"ja-JP|{unique_id}"),
             InlineKeyboardButton("Korean", callback_data=f"ko-KR|{unique_id}")],
            [InlineKeyboardButton("Malay", callback_data=f"ms-MY|{unique_id}"),
             InlineKeyboardButton("Polish", callback_data=f"pl-PL|{unique_id}"),
             InlineKeyboardButton("Portuguese (BR)", callback_data=f"pt-BR|{unique_id}")],
            [InlineKeyboardButton("Portuguese (PT)", callback_data=f"pt-PT|{unique_id}"),
             InlineKeyboardButton("Russian", callback_data=f"ru-RU|{unique_id}"),
             InlineKeyboardButton("Tamil (IN)", callback_data=f"ta-IN|{unique_id}")],
            [InlineKeyboardButton("Telugu (IN)", callback_data=f"te-IN|{unique_id}"),
             InlineKeyboardButton("Thai", callback_data=f"th-TH|{unique_id}"),
             InlineKeyboardButton("Turkish", callback_data=f"tr-TR|{unique_id}")],
            [InlineKeyboardButton("Vietnamese", callback_data=f"vi-VN|{unique_id}"),
             InlineKeyboardButton("Chinese (CN)", callback_data=f"zh-CN|{unique_id}"),
             InlineKeyboardButton("Chinese (TW)", callback_data=f"zh-TW|{unique_id}")],
            [InlineKeyboardButton("All", callback_data=f"all|{unique_id}")]
        ])

        await message.reply("Please select the language:", reply_markup=keyboard)

    except Exception as e:
        await message.reply(f'Error: {str(e)}')
        logger.exception(f'Error: {str(e)}')

@app.on_callback_query()
async def callback_handler(client, callback_query):
    try:
        message = callback_query.message
        callback_data = callback_query.data
        selected_language, unique_id = callback_data.split('|')
        crunchyroll_link = link_store.get(unique_id)

        if not crunchyroll_link:
            await callback_query.message.reply("Error: Link not found.")
            return

        logger.info(f'User selected language: {selected_language} for link: {crunchyroll_link}')

        await message.delete()

        if selected_language == "all":
            language_option = ""
        else:
            language_option = selected_language

        await callback_query.message.reply("Ripping process started...")
        ripped_video = await execute_crunchy_command(crunchyroll_link, callback_query.message, language_option)

        if ripped_video:
            await app.send_video(callback_query.message.chat.id, ripped_video, caption="Here is your ripped video!")
            logger.info(f'Successfully uploaded video to {callback_query.message.chat.id}')
        else:
            await callback_query.message.reply("Ripping process failed. Please try again later.")

    except Exception as e:
        await callback_query.message.reply(f'Error: {str(e)}')
        logger.exception(f'Error: {str(e)}')

def humanbytes(size):
    if not size:
        return ""
    power = 1024
    t_n = 0
    power_dict = {0: ' ', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        t_n += 1
    return "{:.2f} {}B".format(size, power_dict[t_n])

def TimeFormatter(seconds: float) -> str:
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    time_str = ((str(days) + "d, ") if days else "") + \
               ((str(hours) + "h, ") if hours else "") + \
               ((str(minutes) + "m, ") if minutes else "") + \
               ((str(seconds) + "s, ") if seconds else "")
    return time_str[:-2]

app.run()
