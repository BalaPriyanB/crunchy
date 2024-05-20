import logging
from telethon import TelegramClient, events
from config import Config
import asyncio
import subprocess
import time
import math
from telethon.tl.types import InlineKeyboardButton, InlineKeyboardMarkup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

client = TelegramClient('bot_session', Config.TELEGRAM_API_ID, Config.TELEGRAM_API_HASH).start(bot_token=Config.TELEGRAM_BOT_TOKEN)

async def progress_for_pyrogram(current, total, client, message, start_time):
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
            await client.edit_message_text(chat_id=message.chat.id, message_id=message.id, text=progress_message)
    except Exception as e:
        logger.error(f'Error in progress_for_pyrogram: {e}')

async def execute_crunchy_command(crunchyroll_link, message, language_option):
    try:
        command = ['./crunchy-cli-v3.6.3-linux-x86_64',
                   '--anonymous', 'archive', '-r', '1280x720', '-a', language_option,
                   crunchyroll_link]
        process = await asyncio.create_subprocess_exec(*command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        start_time = time.time()
        progress_message = await client.send_message(message.chat_id, "Ripping in progress...")

        while True:
            data = await process.stdout.read(1024)
            if not data:
                break
            await progress_for_pyrogram(process.stdout.tell(), 1000, client, progress_message, start_time)

        stdout, stderr = await process.communicate()

        if process.returncode == 0:
            return stdout
        else:
            logger.error(f'Error executing command: {stderr.decode()}')
            return None
    except Exception as e:
        logger.exception(f'Error executing command: {str(e)}')
        return None


@client.on(events.NewMessage(pattern='/rip'))
async def handle_rip_command(event):
    try:
        crunchyroll_link = event.raw_text.split('/rip', 1)[1].strip()
        logger.info(f'Received rip command for {crunchyroll_link}')

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Arabic (ME)", callback_data="ar-ME"),
             InlineKeyboardButton("Arabic (SA)", callback_data="ar-SA"),
             InlineKeyboardButton("Catalan", callback_data="ca-ES")],
            [InlineKeyboardButton("German", callback_data="de-DE"),
             InlineKeyboardButton("English (IN)", callback_data="en-IN"),
             InlineKeyboardButton("English (US)", callback_data="en-US")],
            [InlineKeyboardButton("Spanish (419)", callback_data="es-419"),
             InlineKeyboardButton("Spanish (ES)", callback_data="es-ES"),
             InlineKeyboardButton("Spanish (LA)", callback_data="es-LA")],
            [InlineKeyboardButton("French", callback_data="fr-FR"),
             InlineKeyboardButton("Hindi (IN)", callback_data="hi-IN"),
             InlineKeyboardButton("Indonesian", callback_data="id-ID")],
            [InlineKeyboardButton("Italian", callback_data="it-IT"),
             InlineKeyboardButton("Japanese", callback_data="ja-JP"),
             InlineKeyboardButton("Korean", callback_data="ko-KR")],
            [InlineKeyboardButton("Malay", callback_data="ms-MY"),
             InlineKeyboardButton("Polish", callback_data="pl-PL"),
             InlineKeyboardButton("Portuguese (BR)", callback_data="pt-BR")],
            [InlineKeyboardButton("Portuguese (PT)", callback_data="pt-PT"),
             InlineKeyboardButton("Russian", callback_data="ru-RU"),
             InlineKeyboardButton("Tamil (IN)", callback_data="ta-IN")],
            [InlineKeyboardButton("Telugu (IN)", callback_data="te-IN"),
             InlineKeyboardButton("Thai", callback_data="th-TH"),
             InlineKeyboardButton("Turkish", callback_data="tr-TR")],
            [InlineKeyboardButton("Vietnamese", callback_data="vi-VN"),
             InlineKeyboardButton("Chinese (CN)", callback_data="zh-CN"),
             InlineKeyboardButton("Chinese (TW)", callback_data="zh-TW")],
            [InlineKeyboardButton("All", callback_data="all")]
        ])

        message = await event.respond("Please select the language:")
        await message.edit(reply_markup=keyboard)


        language_names = {
            "ar-ME": "Arabic (ME)", "ar-SA": "Arabic (SA)", "ca-ES": "Catalan",
            "de-DE": "German", "en-IN": "English (IN)", "en-US": "English (US)",
            "es-419": "Spanish (419)", "es-ES": "Spanish (ES)", "es-LA": "Spanish (LA)",
            "fr-FR": "French", "hi-IN": "Hindi (IN)", "id-ID": "Indonesian",
            "it-IT": "Italian", "ja-JP": "Japanese", "ko-KR": "Korean",
            "ms-MY": "Malay", "pl-PL": "Polish", "pt-BR": "Portuguese (BR)",
            "pt-PT": "Portuguese (PT)", "ru-RU": "Russian", "ta-IN": "Tamil (IN)",
            "te-IN": "Telugu (IN)", "th-TH": "Thai", "tr-TR": "Turkish",
            "vi-VN": "Vietnamese", "zh-CN": "Chinese (CN)", "zh-TW": "Chinese (TW)",
            "all": "All"
        }

        async def callback_handler(event):
            nonlocal message
            selected_language = event.data.decode("utf-8")
            logger.info(f'User selected language: {selected_language}')

            await message.delete()
            if selected_language == "all":
                language_option = ""
            else:
                language_option = f"-a {selected_language}"

            await event.respond("Ripping process started...")
            ripped_video = await execute_crunchy_command(crunchyroll_link, event.message, language_option)

            if ripped_video:
                await client.send_file(event.chat_id, ripped_video, caption="Here is your ripped video!")
                logger.info(f'Successfully uploaded video to {event.chat_id}')
            else:
                await event.respond("Ripping process failed. Please try again later.")

        client.on(events.CallbackQuery(data=re.compile(b".*")), callback_handler)

    except Exception as e:
        await event.respond(f'Error: {str(e)}')
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

client.run_until_disconnected()
