from __future__ import annotations

import datetime
import inspect
import io
import pathlib
import platform
import psutil
import re
from enum import Enum
from time import perf_counter
from typing import TYPE_CHECKING, Dict, Optional

import aiohttp
import asqlite
import dateparser
import discord
import docstring_parser
from discord import app_commands, ui, Embed, Member
from discord.ext import commands
from discord.ui import Select
from wavelink import NodeStatus, Pool

from furina import FurinaCog, FurinaCtx
from settings import *
from cogs.utility.views import PaginatedView


if TYPE_CHECKING:
    from furina import FurinaBot

class HelpActionRow(ui.ActionRow):
    """Help Action Row"""
    def __init__(self, *, id = None, bot: FurinaBot):
        super().__init__(id=id)
        self.add_item(HelpSelect(bot))


class HelpSelect(Select):
    """Help Selection Menu"""
    def __init__(self, bot: FurinaBot):
        super().__init__(
            placeholder="Select a category for command list",
            options=[
                discord.SelectOption(
                    label=cog_name, description=cog.__doc__
                ) for cog_name, cog in bot.cogs.items() if cog.__cog_commands__ and cog_name not in ['Hidden', 'Jishaku']
            ]
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction) -> None:
        container = Utils.list_cog_commands(
            cog=self.bot.get_cog(self.values[0]),
            prefix=self.bot.prefixes.get(interaction.guild.id) or DEFAULT_PREFIX,
        )
        container.add_item(ui.Separator()).add_item(HelpActionRow(bot=self.bot))
        await interaction.response.edit_message(view=ui.LayoutView().add_item(container))


class MemberStatus(Enum):
    online  = ":green_circle: `Online`"
    offline = ":black_circle: `Offline`"
    idle    = ":yellow_circle: `Idling`"
    dnd     = ":red_circle: `Do Not Disturb`"


NODE_STATUSES: Dict[NodeStatus, str] = {
    NodeStatus.CONNECTED: ":white_check_mark:",
    NodeStatus.CONNECTING: ":arrows_clockwise:",
    NodeStatus.DISCONNECTED: ":negative_squared_cross_mark:"
}


class Utils(FurinaCog):
    """Utility Commands"""
    async def cog_load(self):
        self.pool = await asqlite.create_pool(pathlib.Path() / 'db' / 'utils.db')
        await self.__update_custom_prefixes()
        return await super().cog_load()

    async def __update_custom_prefixes(self):
        async with self.pool.acquire() as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS custom_prefixes
                (
                    guild_id INTEGER NOT NULL PRIMARY KEY,
                    prefix TEXT NOT NULL
                )
                """)
            prefixes = await db.fetchall("""SELECT * FROM custom_prefixes""")
            self.bot.prefixes = {prefix["guild_id"]: prefix["prefix"] for prefix in prefixes}

    @staticmethod
    def list_cog_commands(*, cog: FurinaCog, prefix: str) -> ui.Container:
        container = ui.Container(
            ui.TextDisplay(f"## {cog.__cog_name__} Commands")
        )
        prefix_commands = ""
        for command in cog.walk_commands():
            if command.hidden:
                continue
            doc = docstring_parser.parse(command.callback.__doc__)
            prefix_commands += f"- **{prefix}{command.qualified_name}:** `{doc.short_description}`\n"

        if prefix_commands:
            container.add_item(ui.TextDisplay("### Prefix commands\n" + prefix_commands))

        slash_commands = ""
        for command in cog.walk_app_commands():
            doc = docstring_parser.parse(command.callback.__doc__)
            slash_commands += f"- **{command.qualified_name}:** `{doc.short_description}`\n"

        if slash_commands:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay(slash_commands))

        if not prefix_commands and not slash_commands:
            container.add_item(ui.TextDisplay("This cog has no commands to show"))
        return container

    @FurinaCog.listener("on_message")
    async def on_mention(self, message: discord.Message) -> None:
        if message.author == self.bot.user:
            return

        if message.content == self.bot.user.mention:
            header = ui.Section(
                ui.TextDisplay("## Miss me that much?"),
                ui.TextDisplay(f"**My prefix is** `{self.bot.prefixes.get(message.guild.id) or DEFAULT_PREFIX}`"),
                ui.TextDisplay(f"**You can also mention me** {self.bot.user.mention}` <command> `"),
                accessory=ui.Thumbnail(self.bot.user.display_avatar.url)
            )
            source_section = ui.Section(
                ui.TextDisplay("### I am also open source"),
                accessory=ui.Button(
                    label="Click me to view source code",
                    style=discord.ButtonStyle.link,
                    url=r"https://github.com/Th4nhZ/FurinaBot/tree/master"
                )
            )
            container = ui.Container(
                header,
                ui.Separator(),
                source_section,
                ui.Separator()
            )
            uptime_td = discord.utils.utcnow() - self.bot.uptime
            uptime: str = f"{uptime_td.days}d {uptime_td.seconds // 3600}h {(uptime_td.seconds // 60) % 60}m"
            bot_latency: str = f"{round(self.bot.latency * 1000)}ms"
            time = perf_counter()
            async with self.pool.acquire() as db:
                await db.fetchone("""SELECT * FROM custom_prefixes LIMIT 1""")
            db_latency = f"{round((perf_counter() - time) * 1000)}ms"
            container.add_item(
                ui.TextDisplay("### More info\n"
                               f"- **Uptime:** `{uptime}`\n"
                               f"- **Bot Latency:** `{bot_latency}`\n"
                               f"- **Database Latency:** `{db_latency}`"
                )
            )
            container.add_item(ui.Separator())
            container.add_item(HelpActionRow(bot=self.bot))
            view = ui.LayoutView().add_item(container)
            await message.channel.send(view=view, reference=message)

    @commands.command(name='ping')
    async def ping_command(self, ctx: FurinaCtx) -> None:
        """Get the bot's pings

        Get latencies of bot to Discord server, to Voice server and to Database.
        For voice, `-1ms` means it is not connected to any voice channels.
        For lavalink node:
        - :white_check_mark: means it is connected.
        - :arrows_clockwise: means it is still trying to connect (maybe the password is wrong).
        - :negative_squared_cross_mark: means it is disconnected.
        """
        bot_latency: float = self.bot.latency
        voice_latency: float | int = ctx.guild.voice_client.ping if ctx.guild.voice_client else -1
        time = perf_counter()
        async with self.pool.acquire() as db:
            await db.execute("""SELECT * from custom_prefixes LIMIT 1""")
        db_latency = perf_counter() - time
        node_statuses = ""
        for i, node in enumerate(Pool.nodes, 1):
            node_statuses += f"**Node {i}:** {NODE_STATUSES[Pool.nodes[node].status]}"
        container = ui.Container(
            ui.TextDisplay("## Pong!"),
            ui.Separator(),
            ui.TextDisplay(f"**Bot Latency:** `{bot_latency * 1000:.2f}ms`\n"
                           f"**Voice Latency:** `{voice_latency}ms`\n"
                           f"**Database Latency:** `{db_latency * 1000:.2f}ms`"),
            ui.TextDisplay("-# Coded by ThanhZ", row=9)
        )
        if node_statuses:
            container.add_item(ui.Separator())
            container.add_item(ui.TextDisplay(node_statuses))
        await ctx.reply(view=ui.LayoutView().add_item(container))

    @commands.command(name="prefix")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def prefix_command(self, ctx: FurinaCtx, prefix: str) -> None:
        """Set the bot prefix

        Can only be used by member with `Manage Server` permission.
        Can **not** be used in DM.
        New prefix cannot be more than 3 characters long.
        Quotation marks *will be cleared*! So `"a."` ~ `a.`
        Set the prefix to either: `clear`, `reset`, `default`, will reset to the default prefix 「`!`」

        Parameters
        ----------
        prefix: str
            - The new prefix
        """
        prefix: str = prefix.strip().replace('"', "").replace("'", "")
        container = ui.Container(ui.TextDisplay("-# Coded by ThanhZ", row=9))
        if len(prefix) > 3 or not prefix:
            container.add_item(ui.TextDisplay(f"{CROSS} **Invalid prefix**"))
            await ctx.reply(view=ui.LayoutView().add_item(container))
            return
        async with self.pool.acquire() as db:
            if prefix in ['clear', 'reset', 'default', DEFAULT_PREFIX]:
                await db.execute(
                    """
                    DELETE FROM custom_prefixes WHERE guild_id = ?
                    """, ctx.guild.id)
            else:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO custom_prefixes (guild_id, prefix) VALUES (?, ?)
                    """, ctx.guild.id, prefix)
        await self.__update_custom_prefixes()
        container.add_item(
            ui.TextDisplay(
                f"{CHECKMARK} **Prefix set to** `{self.bot.prefixes.get(ctx.guild.id) or DEFAULT_PREFIX}`"
            )
        )
        await ctx.reply(view=ui.LayoutView().add_item(container))

    @commands.command(name='source', aliases=['src'])
    async def source_command(self, ctx: FurinaCtx, *, command: Optional[str] = "") -> None:
        """Get the bot source code

        Get the source code of the bot or a specific command.
        Will return a github link to the bot if no command is provided.
        Otherwise will try to return the command source code.

        Parameters
        ----------
        command: Optional[str] = ""
            - The command of which you need the source code
        """
        cmd: Optional[commands.Command] = self.bot.get_command(command.lower())
        file: Optional[discord.File] = None
        if not command:
            res: str = r"https://github.com/th4nhz/FurinaBot"
        elif not cmd:
            res = f"No commands named {command.lower()}"
        else:
            source: str = inspect.getsource(cmd.callback)
            print(source)
            if len(source) >= 1000:
                res = "Source code is too long so I will send a file instead"
                file = discord.File(io.BytesIO(source.encode('utf-8')), filename=f"{cmd.qualified_name}.py")
            else:
                res = f"```py\n{source}\n```"
        await ctx.reply(res, file=file)


    @commands.command(name='help')
    async def help_command(self, ctx: FurinaCtx, *, query: Optional[str] = None) -> None:
        """The help command

        Shows the command list of a category if it is provided.
        Shows the command's info if a command name is provided.
        If no argument is provided, shows the list of categories.

        Parameters
        ----------
        query : Optional[str] = None
            - Category/Command name you need help with
        """
        # !help
        if query is None:
            prefix = self.bot.prefixes.get(ctx.guild.id) or DEFAULT_PREFIX
            header = ui.Section(
                ui.TextDisplay(f"## {self.bot.user.mention} Help Command"),
                ui.TextDisplay("### To get help with a category\n"
                               f"- Use `{prefix}help <category>`\n"),
                ui.TextDisplay("### To get help with a command\n"
                               f"- Use `{prefix}help <command>`"),
                accessory=ui.Thumbnail(self.bot.user.display_avatar.url)
            )
            container = ui.Container(
                header,
                ui.Separator(),
                HelpActionRow(bot=self.bot)
            )
            await ctx.reply(view=ui.LayoutView().add_item(container))
            return

        # !help <CogName>
        cog: FurinaCog = None
        for cog_ in self.bot.cogs.keys():
            if cog_.lower() == query.lower():
                cog = self.bot.get_cog(cog_)
                break
        if cog and cog.__cog_name__ not in ['Hidden', 'Jishaku']:
            container = self.list_cog_commands(cog=cog, prefix=ctx.prefix)
            container.add_item(ui.Separator()).add_item(HelpActionRow(bot=self.bot))
            await ctx.reply(view=ui.LayoutView().add_item(container))
            return

        # !help <Command>
        command = self.bot.get_command(query.lower())
        if command and not command.hidden and command.name != 'jishaku':
            doc = docstring_parser.parse(command.callback.__doc__)
            usage = command.qualified_name
            syntax = ""
            for param in doc.params:
                # usage is
                # command <required> [optional]
                optional = param.is_optional or param.type_name.startswith("Optional") or param.default
                usage += f" {'[' if optional else '<'}{param.arg_name}{']' if optional else '>'}"
                # syntax is
                # param_name : `param_type = default_value`
                #     param description
                syntax += f"\n{param.arg_name}: {param.type_name}"
                syntax += (param.default + "\n") if param.default else "\n"
                syntax += f"    {param.description}\n"

            container = ui.Container(
                ui.TextDisplay("## " + usage),
                ui.TextDisplay(doc.short_description),
                ui.Separator(),
                ui.TextDisplay(doc.long_description),
                ui.Separator(spacing=discord.SeparatorSize.large),
                ui.TextDisplay("-# Coded by ThanhZ", row=9)
            )
            if syntax:
                container.add_item(ui.TextDisplay(f"**Syntax:** ```{syntax}```"))
            aliases = "**Alias(es):** " + ", ".join(alias for alias in command.aliases) if command.aliases else ""
            if aliases:
                container.add_item(ui.Separator())
                container.add_item(ui.TextDisplay(aliases))
            await ctx.reply(view=ui.LayoutView().add_item(container))
        else:
            raise commands.BadArgument("""I don't recognize that command/category""")

    @commands.command(name='vps', hidden=True)
    @commands.is_owner()
    async def vps_command(self, ctx: FurinaCtx) -> None:
        """Get VPS Info"""
        # OS Version
        os_version = platform.platform()

        # CPU Usage
        cpu_percent = psutil.cpu_percent()

        # RAM Usage
        memory_info = psutil.virtual_memory()
        ram_total = round(memory_info.total / (1024 ** 3), 2)
        ram_used = round(memory_info.used / (1024 ** 3), 2)
        ram_available = round(memory_info.available / (1024 ** 3), 2)
        ram_cached = round(ram_total - ram_used - ram_available, 2)

        # Disk Usage
        disk_info = psutil.disk_usage('/')
        disk_total = round(disk_info.total / (1024 ** 3), 2)
        disk_used = round(disk_info.used / (1024 ** 3), 2)
        disk_available = round(disk_info.free / (1024 ** 3), 2)

        embed = self.embed
        embed.title = "VPS Info"
        embed.add_field(name="Operating System", value=os_version)
        embed.add_field(name="CPU Usage", value=f"{cpu_percent}%", inline=False)
        embed.add_field(
            name="RAM Usage",
            value=f'- Total: {ram_total}GB\n'
                  f'- Used: {ram_used}GB\n'
                  f'- Cache: {ram_cached}GB\n'
                  f'- Free: {ram_available}GB',
            inline=False
        )
        embed.add_field(
            name="Disk Usage",
            value=f'- Total: {disk_total}GB\n'
                  f'- Used: {disk_used}GB\n'
                  f'- Free: {disk_available}GB',
            inline=False
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name='userinfo', aliases=['uinfo', 'whois'])
    async def user_info_command(self, ctx: FurinaCtx, member: Optional[Member] = None):
        """Get a user's info

        Shows info about a member, including their name, id, status, roles,...
        Shows your info if no member is provided.

        Parameters
        ----------
        member: Optional[Member] = None
            - A member to get info from
        """
        member = ctx.guild.get_member(member.id if member else ctx.author.id)
        header = ui.Section(
            ui.TextDisplay(f"## {member.display_name}" + (" (Bot)" if member.bot else "")),
            ui.TextDisplay(f"**Username:** `{member}`\n"
                           f"**ID:** `{member.id}`\n"
                           f"**Status:** {MemberStatus[str(member.status)].value}"),
            accessory=ui.Thumbnail(member.display_avatar.url)
        )
        account_created = int(member.created_at.timestamp())
        server_joined = int(member.joined_at.timestamp())
        container = ui.Container(
            header,
            ui.Separator(),
            ui.TextDisplay(f"**Account Created:** <t:{account_created}> or <t:{account_created}:R>"),
            ui.TextDisplay(f"**Server Joined:** <t:{server_joined}> or <t:{server_joined}:R>"),
            ui.TextDisplay(f"**Roles ({len(member.roles) - 1}):** ```{', '.join(role.name for role in reversed(member.roles) if role.name != '@everyone')}```"),
            ui.TextDisplay("-# Coded by ThanhZ", row=9)
        )
        if member.activities:
            container.add_item(ui.Separator())
            _activities = "**Activities:**\n"
            for i, activity in enumerate(member.activities, 1):
                _activities += f"{i}. **{activity.type.name.capitalize()}"
                _activities += f"{':** ' + activity.name if activity.name else '**'}\n"
            container.add_item(ui.TextDisplay(_activities))
        await ctx.reply(view=ui.LayoutView().add_item(container))

    @staticmethod
    async def dictionary_call(word: str) -> PaginatedView:
        """
        Calls the dictionaryapi

        Parameters
        -----------
        `word: str`
            - The word

        Returns
        -----------
        `PaginatedView`
            A view that contains list of embeds and navigate buttons
        """
        embeds: list[Embed] = []
        async with aiohttp.ClientSession() as cs:
            async with cs.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}") as response:
                if response.status == 404:
                    embed = Embed(
                        title=word.capitalize(),
                        description="No definitions found. API call returned 404."
                    ).set_footer(text="Coded by ThanhZ")
                    return PaginatedView(timeout=300, embeds=[embed])
                data: list[dict] = eval(await response.text())

        embed = Embed(title=word.capitalize()).set_footer(text="Coded by ThanhZ")

        for d in data:
            phonetics = d['phonetic'] if 'phonetic' in d \
                else ", ".join([p['text'] for p in d['phonetics'] if 'text' in p])
            # Phiên âm
            embed.description = f"Pronunciation: `{phonetics}`"

            # Định nghĩa
            for meaning in d['meanings']:
                embed.title += f" ({meaning['partOfSpeech']})"
                if meaning['synonyms']:
                    embed.add_field(
                        name="Synonyms:",
                        value=', '.join(meaning['synonyms'])
                    )
                if meaning['antonyms']:
                    embed.add_field(
                        name="Antonyms:",
                        value=', '.join(meaning['antonyms'])
                    )
                definition_value = ""
                for definition in meaning['definitions']:
                    after = definition_value + ("\n- " + definition['definition'])
                    if len(after) < 1024:
                        definition_value = after
                embed.add_field(
                    name="Definition",
                    value=definition_value,
                    inline=False
                )
                embeds.append(embed)
                embed = Embed(
                    title=word.capitalize(),
                    description=f"Pronunciation: `{phonetics}`"
                ).set_footer(text="Coded by ThanhZ")
        return PaginatedView(timeout=300, embeds=embeds)

    @commands.hybrid_command(name='dictionary', aliases=['dict'])
    @app_commands.allowed_installs(guilds=True, users=True)
    async def dict_command(self, ctx: FurinaCtx, word: str):
        """Lookup a word in the dictionary

        Use DictionaryAPI to look up a word.
        Note that it can only look up the first word, every other words after will be ignored.

        Parameters
        ----------
        word: str
            - The word to look up
        """
        view = await self.dictionary_call(word.split()[0])
        view.message = await ctx.reply(embed=view.embeds[0], view=view)

    @commands.command(name='wordoftheday', aliases=['wotd'])
    async def wotd_command(self, ctx: FurinaCtx, *, date: Optional[str] = None):
        """View today's word

        Shows today's, or any day's word of the day.
        Can take any date format, even human friendly ones.
        Like 'yesterday', 'last month',...

        Parameters
        ----------
        date: Optional[str] = None
            - The date to get word of the day from
        """
        date_ = dateparser.parse(
            date if date else datetime.datetime.now(tz=datetime.timezone.utc).strftime(r"%Y-%m-%d"),
            settings={'TIMEZONE': 'UTC', 'RETURN_AS_TIMEZONE_AWARE': True}
        )
        date = date_.strftime(r"%Y-%m-%d")
        day_check = r"202\d-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])"
        if not re.match(day_check, date):
            return await ctx.reply("You entered a very old date, try a newer one")
        ddmmyyyy = date_.strftime(r"%A %d/%m/%Y")
        async with self.bot.cs.get(f"https://api.wordnik.com/v4/words.json/wordOfTheDay?date={date}&api_key={WORDNIK_API}") as response:
            if not response.status == 200:
                return await ctx.reply("Something went wrong")
            content: Dict = await response.json()
        container = ui.Container(
            ui.TextDisplay(f"## {content['word']} ({content['definitions'][0]['partOfSpeech']})"),
            ui.TextDisplay("**Definition:**\n>>> " + content['definitions'][0]['text']),
            ui.Separator(),
            ui.TextDisplay("**Fun fact:**\n" + content['note']),
            ui.TextDisplay(f"-# Coded by ThanhZ | Date: `{ddmmyyyy}`")
        )
        await ctx.reply(view=ui.LayoutView().add_item(container))


async def setup(bot: FurinaBot):
    await bot.add_cog(Utils(bot))