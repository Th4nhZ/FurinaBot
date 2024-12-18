import os
import time
from colorama import Back, Fore, Style
from dotenv import load_dotenv

load_dotenv()

# Basic
PREFIX = "!"
ACTIVITY_NAME = "Music » /play"
TOKEN = os.getenv("BOT_TOKEN")
DEBUG_CHANNEL = 1155196242062753924

# GIF
LOADING_GIF = "https://cdn.discordapp.com/emojis/1187957747724079144.gif?size=64&name=loading&quality=lossless"
PLAYING_GIF = "https://cdn.discordapp.com/emojis/1174925797082017923.gif?size=64&name=playing&quality=lossless"

# Emojis
SKIP_EMOJI = "https://cdn.discordapp.com/emojis/1174966018280529931.png?size=64&name=skip&quality=lossless"

# Emotes
CHECKMARK = "<a:check:1238796460569657375>"

# Print effect
offset = 7 * 3600
timee = time.time() + offset
PRFX = (Back.BLACK + Fore.GREEN + time.strftime("%H:%M:%S", time.localtime(timee)) + Back.RESET + Fore.WHITE +
        Style.BRIGHT)

# Mentioned
MENTIONED_TITLE = "Gọi gì mình ấy, nhớ mình à? :flushed:"
MENTIONED_DESC = ("**- Prefix của mình:** `!` \n"
                  "**- Mình cũng có hỗ trợ slash commands** -> Gõ `/` để xem những lệnh được hỗ trợ!\n"
                  "**- Bạn cũng có thể sử dụng menu bên dưới để xem các lệnh của mình.**")

# Music Cog
MUSIC_CHANNEL = 1089851760425848923
PLAYER_CHANNEL = 1221123310893404241
LAVA_URI = os.getenv("LAVA_URI")
LAVA_BACKUP = os.getenv("LAVA_BACKUP")
LAVA_PW = os.getenv("LAVA_PW")

# Utils Cog
MOMO = os.getenv("MOMO")
PAYPAL = os.getenv("PAYPAL")
BANKING = os.getenv("BANKING")

# Hidden Cog

instance_name = "furina"

# Edit this if you are using different package manager, I'm using PM2
REBOOT_CMD = f"pm2 start {instance_name}"

# Edit this if your logs file location is different, since I'm using pm2 and host the bot on AWS
# the logs file is at /home/ubuntu/.pm2/logs/{instance_name}-error.log
LOG_FILE = f"/home/ubuntu/.pm2/logs/{instance_name}-error.log"


