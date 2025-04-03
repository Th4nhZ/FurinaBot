from __future__ import annotations

import aiohttp
import asyncio
import asyncpg
import platform
import psutil
import random
from enum import Enum
from typing import TYPE_CHECKING, Dict, Optional

import discord
import wavelink
from discord import app_commands, Color, Embed, Message
from discord.ext import commands
from discord.ui import Select
from wavelink import NodeStatus, Pool

from bot import FurinaCtx
from settings import *
from cogs.utility.views import PaginatedView, View
from cogs.utility.sql import PrefixSQL, TagSQL


if TYPE_CHECKING:
    from bot import FurinaBot


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
        await interaction.response.send_message(embed=embed, ephemeral=True)


class MemberStatus(Enum):
    online  = ":green_circle: `Online`"
    offline = ":black_circle: `Offline`"
    idle    = ":yellow_circle: `Idling`"
    dnd     = ":red_circle: `DND`"
    

NODE_STATUSES: Dict[NodeStatus, str] = {
    NodeStatus.CONNECTED: ":white_check_mark:",
    NodeStatus.CONNECTING: ":arrows_clockwise:",
    NodeStatus.DISCONNECTED: ":negative_squared_cross_mark:"
}


class Utils(commands.Cog):
    """Utility Commands"""
    def __init__(self, bot: FurinaBot):
        self.bot = bot

    @property
    def embed(self) -> Embed:
        return self.bot.embed
    
    @staticmethod
    def command_list_embed(*, cog: commands.Cog, prefix: str, embed: Embed) -> Embed:
        embed.title = cog.__cog_name__
        embed.description = "\n".join(
            f"- **{prefix}{command.qualified_name}:** `{command.description}`"
            for command in cog.walk_commands()
        )
        return embed
    
    async def cog_load(self) -> None:
        await TagSQL(pool=self.bot.pool).create_tag_table()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
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
            embed.add_field(name="More info", value=f"Uptime: `{uptime}`\nPing: `{api_ping}`")
            embed.timestamp = message.created_at
            view = View().add_item(HelpSelect(self.bot))
            view.message = await message.channel.send(embed=embed, view=view, reference=message)

    @staticmethod
    def generate_random_number(min_num: int, max_num: int) -> int:
        random_number: int = -1
        for _ in range(100):
            random_number = random.randint(min_num, max_num)
        return random_number

    @commands.command(name='ping', description="Get the ping to discord api and lavalink nodes")
    async def ping_command(self, ctx: FurinaCtx):
        await ctx.defer()
        bot_latency = self.bot.latency
        voice_latency = ctx.guild.voice_client.ping if ctx.guild.voice_client else -1

        embed = self.embed
        embed.title = "Pong!"
        embed.add_field(name="Ping:", value=f"**Text:** {bot_latency * 1000:.2f}ms\n**Voice:** {voice_latency}ms")

        for i, node in enumerate(Pool.nodes, 1):
            node_ = wavelink.Pool.get_node(node)
            node_status = NODE_STATUSES[node_.status]
            embed.add_field(name=f"Node {i}: {node_status}", value="", inline=False)
        await ctx.reply(embed=embed)

    @commands.command(name="prefix", description="Set a custom prefix for your server")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    async def prefix_command(self, ctx: FurinaCtx, prefix: str):
        await ctx.tick()
        if prefix in ['clear', 'reset', 'default', DEFAULT_PREFIX]:
            await PrefixSQL(pool=self.bot.pool).delete_custom_prefix(guild_id=ctx.guild.id)
        else:
            await PrefixSQL(pool=self.bot.pool).set_custom_prefix(guild_id=ctx.guild.id, prefix=prefix)
        await self.bot.update_prefixes()
        embed = ctx.embed
        embed.description = f"Prefix for this server has been changed to `{self.bot.prefixes.get(ctx.guild.id) or DEFAULT_PREFIX}`"
        await ctx.reply(embed=embed)

    @commands.command(name='source', aliases=['sources', 'src'], description="Source code of the bot")
    async def source_command(self, ctx: FurinaCtx):
        await ctx.reply("https://github.com/Th4nhZ/FurinaBot")

    @commands.command(name='help', description="Help command")
    async def help_command(self, ctx: FurinaCtx, category_or_command_name: str = None):
        """
        Parameters
        -----------
        category_or_command_name: `str`
            Category/Command name you need help with
        """
        # !help
        if category_or_command_name is None:
            view = View().add_item(HelpSelect(self.bot))
            view.message = await ctx.reply(view=view)
            return
        
        # !help <CogName>
        cog: commands.Cog = None
        for cog_ in self.bot.cogs.keys():
            if cog_.lower() == category_or_command_name.lower():
                cog = self.bot.get_cog(cog_)
                break
        if cog and cog.__cog_name__ not in ['Hidden', 'Jishaku']:
            embed = self.command_list_embed(cog=cog, prefix=ctx.prefix, embed=self.embed)
            return await ctx.reply(embed=embed)
        
        # !help <Command>
        command = self.bot.get_command(category_or_command_name.lower())
        if command and not command.hidden and command.name != 'jishaku':
            embed = self.embed
            embed.description = (f"- **__Name:__** `{command.qualified_name}`\n"
                                 f"- **__Description:__** {command.description}\n"
                                 f"- **__How to use:__** `{ctx.prefix}{command.qualified_name} {command.signature}`")
            embed.set_footer(text="Aliases: " + ", ".join(alias for alias in command.aliases) if command.aliases else "")
            await ctx.reply(embed=embed)
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

    @commands.hybrid_command(name='userinfo', aliases=['uinfo', 'whois'], description="Get info about a member")
    async def user_info_command(self, ctx: FurinaCtx, member: Optional[discord.Member] = None):
        """
        Parameters
        -----------
        member: `Optional[discord.Member]`
            A member to get info from
        """
        member = ctx.guild.get_member(member.id if member else ctx.author.id)
        embed = self.embed
        embed.title = "Member Info"
        embed.color = Color.blue()
        embed.add_field(name="Display Name:", value=member.mention)
        embed.add_field(name="Username:", value=member)
        embed.add_field(name="ID:", value=member.id)
        embed.set_thumbnail(url=member.display_avatar.url)
        account_created = int(member.created_at.timestamp())
        embed.add_field(name="Account Created:", value=f"<t:{account_created}>\n<t:{account_created}:R>")
        server_joined = int(member.joined_at.timestamp())
        embed.add_field(name="Server Joined:", value=f"<t:{server_joined}>\n<t:{server_joined}:R>")
        embed.add_field(name="Status: ", value=MemberStatus[str(member.status)].value)
        embed.add_field(name="Roles:", value=", ".join(role.mention for role in reversed(member.roles) if role.name != '@everyone'))
        if member.activity:
            embed.add_field(
                name="Activity:",
                value=f"**{str.capitalize(member.activity.type.name)}**: `{member.activity.name}`"
                if member.activity.name != None else "`None`"
            )
        embed.timestamp = ctx.message.created_at
        await ctx.reply(embed=embed)

    @commands.command(name='fortune', aliases=['lucky', 'slip', 'fortuneslip'], description="Draw a fortune slip")
    async def fortune_slip(self, ctx: FurinaCtx, number: Optional[int] = 1) -> None:
        fortune_convert = {
            0: {
                "name": "Miss Fortune",
                "color": discord.Color.darker_gray()
            },
            1: {
                "name": "Miss Fortune",
                "color": discord.Color.darker_gray()
            },
            2: {
                "name": "Miss Fortune",
                "color": discord.Color.darker_gray()
            },
            3: {
                "name": "Miss Fortune",
                "color": discord.Color.darker_gray()
            },
            4: {
                "name": "Rising Fortune",
                "color": discord.Color.dark_purple()
            },
            5: {
                "name": "Rising Fortune",
                "color": discord.Color.dark_purple()
            },
            6: {
                "name": "Rising Fortune",
                "color": discord.Color.dark_purple()
            },
            7: {
                "name": "Rising Fortune",
                "color": discord.Color.dark_purple()
            },
            8: {
                "name": "Fortune",
                "color": discord.Color.pink()
            },
            9: {
                "name": "Fortune",
                "color": discord.Color.pink()
            },
            10: {
                "name": "Grand Fortune",
                "color": discord.Color.red()
            },
        }
        embed = self.bot.embed
        if number == 1:
            rand_num = self.generate_random_number(0, 10)
        else:
            best: int = 0
            for i in range(number - 1):
                rand_num = self.generate_random_number(0, 10)
                best = max(best, rand_num)
            embed.description = f"They couldve got {fortune_convert[best]['name']} if they were more thoughtful"
        embed.color = fortune_convert[rand_num]["color"]
        embed.title = fortune_convert[rand_num]["name"]
        embed.set_author(name=f"{ctx.author.display_name} thought {number} times before drawing a fortune slip",
                         icon_url="https://cdn.7tv.app/emote/6175d52effc7244d797d15bf/4x.gif")
        await ctx.send(embed=embed)

    @commands.command(name='dice', aliases=['roll'], description="Roll a dice 6")
    async def dice(self, ctx: FurinaCtx, number: Optional[int] = 1) -> None:
        embed = discord.Embed()
        if number == 1:
            rand_num = self.generate_random_number(1, 6)
        else:
            seq = ""
            for i in range(number):
                rand_num = self.generate_random_number(1, 6)
                seq += f"{rand_num} "
            embed.add_field(name="History:", value=f"```\n{seq[:-1]}\n```")
        embed.set_author(name=f"{ctx.author.display_name} rolled a dice {number} times",
                         icon_url="https://cdn.7tv.app/emote/6175d52effc7244d797d15bf/4x.gif")
        embed.title = f"The current number is: {rand_num}"
        await ctx.send(embed=embed)

    @commands.command(name='flip', aliases=['coin', 'coinflip'], description="Flip a coin")
    async def flip(self, ctx: FurinaCtx, number: Optional[int] = 1) -> None:
        embed = discord.Embed()
        if number == 1:
            for _ in range(100):
                rand_flip = random.choice(["Head", "Tail"])
        else:
            seq = ""
            for i in range(number):
                for i in range(100):
                    rand_flip = random.choice(["Head", "Tail"])
                seq += f"{rand_flip[:-3]} "
            embed.add_field(name="History:", value=f"```\n{seq[:1000]}...\n```")
        embed.set_author(name=f"{ctx.author.display_name} flipped a coin {number} times",
                         icon_url="https://cdn.7tv.app/emote/6175d52effc7244d797d15bf/4x.gif")
        embed.title = f"{rand_flip}"
        await ctx.send(embed=embed)

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

    @commands.hybrid_command(name='dictionary', aliases=['dict'], description="Find a word in the dictionary")
    @app_commands.allowed_installs(guilds=True, users=True)
    async def dict_command(self, ctx: FurinaCtx, word: str):
        """
        Find a word in the dictionary
        
        Parameters
        -----------
        word: `str`
            - The word, note that it only get the first word
        """
        view = await self.dictionary_call(word.split()[0])
        view.message = await ctx.reply(embed=view.embeds[0], view=view)

    @commands.group(name='tag', description="Tags related command")
    @commands.guild_only()
    async def tag_command(self, ctx: FurinaCtx,
                          action: str = None,
                          *,
                          name: str = None):
        """Tags related command

        Parameters
        ----------
        action: `str = None`
            - create/delete/edit/info a tag
        name: `str = None`
            - just for help command
        """
        if action == 'create':
            return await self.__create_tag(ctx, name)
        if action == 'delete':
            return await self.__delete_tag(ctx, name)
        if action == 'edit':
            return await self.__edit_tag()
        name = action + " " + name if name else action
        tag = await TagSQL(pool=ctx.pool).get_tag(guild_id=ctx.guild.id, name=name)
        if not tag:
            await ctx.send(f"No tags found for query: `{name}`")
        else:
            await ctx.send(tag)
            
    async def __create_tag(self, ctx: FurinaCtx, data: str = None):
        def check(m: Message):
            return (m.author == ctx.author and 
                    m.channel == ctx.channel and 
                    m.content != "" and 
                    not m.content.startswith((self.bot.prefixes.get(ctx.guild.id) or DEFAULT_PREFIX, self.bot.user.mention)))
        if not data:
            try:
                pending = await ctx.send("What is the name of the tag?")
                name: Message = await self.bot.wait_for('message', check=check, timeout=60)
                pending = await ctx.send("What is the content of the tag?")
                content: Message = await self.bot.wait_for('message', check=check, timeout=300)
                await TagSQL(pool=self.bot.pool).create_tag(guild_id=ctx.guild.id, owner=ctx.author.id, name=name.content, content=content.content)
                return await ctx.send(f"Tag `{name.content}` created!")
            except asyncio.TimeoutError:
                await ctx.send("Timed out waiting for input. Cancelling tag creation...", reference=pending)
            except asyncpg.UniqueViolationError:
                await ctx.send(f"Tag `{name.content}` already exists`")
        # TODO: get the name and content out of the data
            
    async def __delete_tag(self, ctx: FurinaCtx, name: str):
        if ctx.author.guild_permissions.manage_guild:
            result = await TagSQL(pool=self.bot.pool).force_delete_tag(guild_id=ctx.guild.id, name=name)
        else:
            result = await TagSQL(pool=self.bot.pool).delete_tag(guild_id=ctx.guild.id, owner=ctx.author.id, name=name)
        await ctx.send(result)
    
    async def __edit_tag(self):
        raise NotImplemented

    @tag_command.command(name="create", description="Create a tag")
    async def tag_create(self, ctx: FurinaCtx, name: str, *, content: str):
        """Create a tag

        This is just a placeholder for help command

        Parameters
        ----------
        name: `str`
            - The name of the tag
        content: `str`
            - The content of the tag
        """
        pass
        
    @tag_command.command(name="delete", description="Delete a tag")
    async def tag_delete(self, ctx: FurinaCtx, name: str):
        """Delete a tag

        This is just a placeholder for help command

        Parameters
        ----------
        name: `str`
            - The name of the tag
        """
        pass

    @tag_command.command(name="edit", description="Edit a tag")
    async def tag_edit(self, ctx: FurinaCtx, name: str, *, content: str):
        """Edit a tag

        This is just a placeholder for help command

        Parameters
        ----------
        name: `str`
            - The name of the tag
        content: `str`
            - The new content of the tag
        """
        pass

async def setup(bot: FurinaBot):
    await bot.add_cog(Utils(bot))