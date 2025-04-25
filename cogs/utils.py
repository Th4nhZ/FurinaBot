from __future__ import annotations

import datetime
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
from discord import app_commands, ui, Color, Embed, Member
from discord.ext import commands
from discord.ui import Select
from wavelink import NodeStatus, Pool

from furina import FurinaCog, FurinaCtx
from settings import *
from cogs.utility.views import PaginatedView, View


if TYPE_CHECKING:
    from furina import FurinaBot


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
        embed = Utils.command_list_embed(
            cog=self.bot.get_cog(self.values[0]),
            prefix=self.bot.prefixes.get(interaction.guild.id) or DEFAULT_PREFIX,
            embed=self.bot.embed
        )
        await interaction.response.edit_message(embed=embed)


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
    def command_list_embed(*, cog: FurinaCog, prefix: str, embed: Embed) -> Embed:
        embed.title = cog.__cog_name__
        embed.description = "\n".join(
            f"- **{prefix}{command.qualified_name}:** `{command.description}`"
            for command in cog.walk_commands()
        )
        return embed

    @FurinaCog.listener("on_message")
    async def on_mention(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if message.content == self.bot.user.mention:
            embed = self.embed
            embed.description = self.bot.application.description
            embed.color = Color.blue()
            embed.set_author(
                name="Miss me that much?",
                icon_url="https://cdn.7tv.app/emote/01HHV72FBG000870SVK5KGTSJM/4x.png"
            )
            embed.add_field(name=f"My prefix is `{self.bot.prefixes.get(message.guild.id) or DEFAULT_PREFIX}`",
                            value=f"You can also mention me\n{self.bot.user.mention}` <command> `")
            embed.add_field(name="I am also open source", value="[**My repository**](https://github.com/Th4nhZ/FurinaBot/tree/master)")
            uptime_td = discord.utils.utcnow() - self.bot.uptime
            uptime: str = f"{uptime_td.days}d {uptime_td.seconds // 3600}h {(uptime_td.seconds // 60) % 60}m"
            api_ping: str = f"{round(self.bot.latency * 1000)}ms"
            time = perf_counter()
            async with self.pool.acquire() as db:
                await db.fetchone("""SELECT 1""")
            db_ping = f"{round((perf_counter() - time) * 1000)}ms"
            embed.add_field(name="More info",
                            value=f"Uptime: `{uptime}`\nAPI Ping: `{api_ping}`\nDatabase Ping: `{db_ping}`")
            embed.timestamp = message.created_at
            view = View().add_item(HelpSelect(self.bot))
            view.message = await message.channel.send(embed=embed, view=view, reference=message)

    @commands.command(name='ping', description="Get the ping to discord api and lavalink nodes")
    async def ping_command(self, ctx: FurinaCtx):
        await ctx.defer()
        bot_latency = self.bot.latency
        voice_latency = ctx.guild.voice_client.ping if ctx.guild.voice_client else -1
        time = perf_counter()
        async with self.pool.acquire() as db:
            await db.execute("""SELECT 1""")
        db_latency = perf_counter() - time

        embed = self.embed
        embed.title = "Pong!"
        embed.add_field(name="Ping:", value=f"**Text:** {bot_latency * 1000:.2f}ms\n**Voice:** {voice_latency}ms\n**Database:** {db_latency * 1000:.2f}ms")

        for i, node in enumerate(Pool.nodes, 1):
            node_ = Pool.get_node(node)
            node_status = NODE_STATUSES[node_.status]
            embed.add_field(name=f"Node {i}: {node_status}", value="", inline=False)
        await ctx.reply(embed=embed)

    @commands.command(name="prefix", description="Set a custom prefix for your server")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def prefix_command(self, ctx: FurinaCtx, prefix: str):
        prefix = prefix.strip().replace('"', "").replace("'", "")
        embed = self.embed
        async with self.pool.acquire() as db:
            if prefix in ['clear', 'reset', 'default', DEFAULT_PREFIX]:
                await db.execute("""DELETE FROM custom_prefixes WHERE guild_id = ?""", ctx.guild.id)
            else:
                if len(prefix) > 3 or not prefix:
                    await ctx.cross()
                    embed.description = "Prefix is too long or is empty, try again with different prefix"
                    return await ctx.reply(embed=embed)
                await db.execute(
                    """
                    INSERT OR REPLACE INTO custom_prefixes (guild_id, prefix) VALUES (?, ?)
                    """, ctx.guild.id, prefix)
            await db.commit()
        await self.__update_custom_prefixes()
        await ctx.tick()
        embed.description = f"Prefix for this server has been changed to `{self.bot.prefixes.get(ctx.guild.id) or DEFAULT_PREFIX}`"
        await ctx.reply(embed=embed)

    @commands.command(name='source', aliases=['sources', 'src'], description="Source code of the bot")
    async def source_command(self, ctx: FurinaCtx):
        await ctx.reply("https://github.com/Th4nhZ/FurinaBot")

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
            embed = self.embed.set_author(name="Help Command", icon_url=ctx.author.display_avatar.url)
            view = View().add_item(HelpSelect(self.bot))
            view.message = await ctx.reply(embed=embed, view=view)
            return

        # !help <CogName>
        cog: FurinaCog = None
        for cog_ in self.bot.cogs.keys():
            if cog_.lower() == query.lower():
                cog = self.bot.get_cog(cog_)
                break
        if cog and cog.__cog_name__ not in ['Hidden', 'Jishaku']:
            embed = self.command_list_embed(cog=cog, prefix=ctx.prefix, embed=self.embed)
            await ctx.reply(embed=embed)
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
                syntax += f"```\n{param.arg_name}: {param.type_name}"
                syntax += (param.default + "\n") if param.default else "\n"
                syntax += f"    {param.description}\n```"

            container = ui.Container(
                ui.TextDisplay("## " + usage),
                ui.TextDisplay(doc.short_description),
                ui.Separator(),
                ui.TextDisplay(doc.long_description),
                ui.Separator(spacing=discord.SeparatorSize.large),
                ui.TextDisplay("**Syntax:**\n" + syntax),
            )
            aliases = "**Alias(es):** " + ", ".join(alias for alias in command.aliases) if command.aliases else ""
            if aliases:
                container.add_item(ui.Separator())
                container.add_item(ui.TextDisplay(aliases))
            container.add_item(ui.TextDisplay("-# Coded by ThanhZ"))
            await ctx.reply(view=ui.LayoutView().add_item(container))
        else:
            raise commands.BadArgument("""I don't recognize that command/category""")

    @commands.command(name='vps', hidden=True, description="VPS Info")
    @commands.is_owner()
    async def vps_command(self, ctx: FurinaCtx):
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
        section = ui.Section(
            f"**Username:** `{member}`",
            f"**ID:** `{member.id}`",
            f"**Status:** {MemberStatus[str(member.status)].value}",
            accessory=ui.Thumbnail(member.display_avatar.url)
        )
        account_created = int(member.created_at.timestamp())
        server_joined = int(member.joined_at.timestamp())
        container = ui.Container(
            ui.TextDisplay(f"## {member.display_name}" + (" (Bot)" if member.bot else "")),
            section,
            ui.Separator(),
            ui.TextDisplay(f"**Account Created:** <t:{account_created}> or <t:{account_created}:R>"),
            ui.TextDisplay(f"**Server Joined:** <t:{server_joined}> or <t:{server_joined}:R>"),
            ui.TextDisplay(f"**Roles ({len(member.roles) - 1}):** ```{', '.join(role.name for role in reversed(member.roles) if role.name != '@everyone')}```")
        )
        if member.activities:
            container.add_item(ui.Separator())
            _activities = "**Activities:**\n"
            for i, activity in enumerate(member.activities, 1):
                _activities += f"{i}. **{activity.type.name.capitalize()}"
                _activities += f"{':** ' + activity.name if activity.name else '**'}\n"
            container.add_item(ui.TextDisplay(_activities))
        container.add_item(ui.TextDisplay("-# Coded by ThanhZ"))
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