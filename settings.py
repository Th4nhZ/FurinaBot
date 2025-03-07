import os
from dotenv import load_dotenv

load_dotenv()

# Basic
DEFAULT_PREFIX = "!"
ACTIVITY_NAME = "Music » /play"
TOKEN = os.getenv("BOT_TOKEN")
DEBUG_WEBHOOK = os.getenv("DEBUG_WEBHOOK")

# GIF
LOADING_GIF = "https://cdn.discordapp.com/emojis/1187957747724079144.gif?size=64&name=loading&quality=lossless"
PLAYING_GIF = "https://cdn.discordapp.com/emojis/1174925797082017923.gif?size=64&name=playing&quality=lossless"

# Emojis
SKIP_EMOJI = "https://cdn.discordapp.com/emojis/1174966018280529931.png?size=64&name=skip&quality=lossless"

# Emotes
CHECKMARK = "<a:check:1238796460569657375>"

# Music Cog
MUSIC_CHANNEL = 1089851760425848923
MUSIC_WEBHOOK = os.getenv("MUSIC_WEBHOOK")
LAVA_URI = "http://localhost:1710"
LAVA_PW = "thanhz"
BACKUP_LL = os.getenv("BACKUP_LL")
BACKUP_LL_PW = os.getenv("BACKUP_LL_PW")
