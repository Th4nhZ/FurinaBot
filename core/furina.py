"""
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import annotations

import logging
import typing
from platform import python_version

import discord
import wavelink
from discord import app_commands, ui, utils
from discord.ext import commands
from discord.ext.commands import errors, when_mentioned_or

from cogs import EXTENSIONS
from core import settings

if typing.TYPE_CHECKING:
    import aiohttp


class FurinaCtx(commands.Context):
    """Custom Context class with some shortcuts"""
    def __init__(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        self.bot: FurinaBot
        self.message: discord.Message

    async def tick(self) -> None:
        """Reacts checkmark to the command message"""
        try:
            await self.message.add_reaction(settings.CHECKMARK)
        except discord.HTTPException:
            pass

    async def cross(self) -> None:
        """Reacts a cross to the command message"""
        try:
            await self.message.add_reaction(settings.CROSS)
        except discord.HTTPException:
            pass

    @property
    def cs(self) -> aiohttp.ClientSession:
        """Shortcut for `FurinaBot.cs`"""
        return self.bot.cs

    @property
    def embed(self) -> discord.Embed:
        """Shortcut for FurinaBot.embed"""
        return self.bot.embed


class FurinaBot(commands.Bot):
    """
    Customized `commands.Bot` class

    Attributes
    ----------
    client_session : :obj:`aiohttp.ClientSession`
        Aiohttp client session for making requests
    skip_lavalink : :obj:`bool`
        Whether to skip Lavalink or not

    Usage
    -----
    .. code-block:: python
        async with aiohttp.ClientSession() as client_session:
            async with FurinaBot(client_session=client_session, skip_lavalink=True) as bot:
                await bot.start(TOKEN)
    """

    DEFAULT_PREFIX: str = settings.DEFAULT_PREFIX
    
    def __init__(self, *, client_session: aiohttp.ClientSession, skip_lavalink: bool) -> None:
        super().__init__(
            command_prefix=self.get_pre,
            case_insensitive=True,
            strip_after_prefix=True,
            intents=discord.Intents.all(),
            help_command=None,
            allowed_contexts=app_commands.AppCommandContext(
                dm_channel=False,
                guild=True
            ),
            activity=discord.Activity(
                type=discord.ActivityType.playing,
                name=settings.ACTIVITY_NAME
            )
        )
        self.owner_id = settings.OWNER_ID
        self.skip_lavalink = skip_lavalink
        self.cs = client_session
        self.prefixes: dict[int, str] = {}

    @property
    def container(self) -> ui.Container:
        """Container with default 'footer'"""
        return ui.Container(
            ui.TextDisplay("-# Coded by ThanhZ", row=39)
        )

    @property
    def embed(self) -> discord.Embed:
        """Embed with default footer"""
        return discord.Embed().set_footer(text="Coded by ThanhZ")

    @property
    def uptime(self) -> str:
        uptime_td = utils.utcnow() - self._startup
        return f"`{uptime_td.days}d {uptime_td.seconds // 3600}h {(uptime_td.seconds // 60) % 60}m`"

    async def get_context(self,
                          message: discord.Message,
                          *,
                          cls: FurinaCtx = FurinaCtx) -> FurinaCtx:
        return await super().get_context(message, cls=cls)

    def get_pre(self, _: FurinaBot, message: discord.Message) -> list[str]:
        """Custom `get_prefix` method"""
        if not message.guild:
            return when_mentioned_or(self.DEFAULT_PREFIX)(self, message)
        prefix = self.prefixes.get(message.guild.id) or self.DEFAULT_PREFIX
        return when_mentioned_or(prefix)(self, message)

    async def on_ready(self) -> None:
        logging.info("Logged in as %s", self.user.name)
        self._startup = utils.utcnow()

        try:
            embed = self.embed.set_author(name="BOT IS READY!")
            embed.color = self.user.accent_color
            embed.timestamp = utils.utcnow()
            webhook = discord.Webhook.from_url(settings.DEBUG_WEBHOOK, client=self)
            await webhook.send(embed=embed,
                               avatar_url=self.user.display_avatar.url,
                               username=self.user.display_name)
        except ValueError:
            logging.warning(
                "Cannot get the Webhook url for on_ready events."
                "If you don't want to get a webhook message when the bot is ready,"
                "please ignore this"
            )

    async def setup_hook(self) -> None:
        logging.info("discord.py v%s", discord.__version__)
        logging.info("Wavelink v%s", wavelink.__version__)
        logging.info("Running Python %s", python_version())
        logging.info("Fetching bot emojis")
        self.app_emojis: list[discord.Emoji] = await self.fetch_application_emojis()

        # loads the extensions
        logging.info("Loading extensions")
        for extension in EXTENSIONS:
            extension_name = extension[5:]
            try:
                await self.load_extension(f"{extension}")
            except errors.NoEntryPointError:
                logging.exception(
                    "Extension %s has no setup function so it cannot be loaded", extension_name
                )
            except Exception:
                logging.exception("An error occured when trying to load %s", extension_name)
        await self.load_extension("jishaku")
        logging.info("Loaded Jishaku extension")

    async def start(self) -> None:
        return await super().start(settings.TOKEN, reconnect=True)


class FurinaCog(commands.Cog):
    """Base class for all cogs"""
    def __init__(self, bot: FurinaBot) -> None:
        self.bot = bot

    async def cog_load(self) -> None:
        logging.info("Cog %s has been loaded", self.__cog_name__)

    @property
    def embed(self) -> discord.Embed:
        """Shortcut for `FurinaBot.embed`"""
        return self.bot.embed

    @property
    def container(self) -> ui.Container:
        """Shortcut for `FurinaBot.container`"""
        return self.bot.container
