from __future__ import annotations

import aiosqlite, platform, discord, random, psutil, wavelink, aiohttp
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Optional, List
from discord.ui import Select


from _classes.embeds import *
from _classes.views import PaginatedView, TimeoutView, SelectView

if TYPE_CHECKING:
    from bot import Furina


class HelpSelect(Select):
    """Help Selection Menu"""
    def __init__(self, bot: Furina):
        super().__init__(
            placeholder="Select Category",
            options=[
                discord.SelectOption(
                    label=cog_name, description=cog.__doc__
                ) for cog_name, cog in bot.cogs.items() if cog.__cog_commands__ and cog_name not in ['Hidden']
            ]
        )
        self.bot = bot

    async def callback(self, interaction: discord.Interaction) -> None:
        cog = self.bot.get_cog(self.values[0])
        assert cog

        commands_mixer: List[commands.Command] = []

        for i in cog.walk_commands():
            commands_mixer.append(i)

        embed = FooterEmbed()
        embed.title = "To see more detail about a specific command, use `!help <command_name>`"
        embed.description = "\n".join(
            f"- **{DEFAULT_PREFIX}{command.qualified_name}:** `{command.description}`"
            for command in commands_mixer
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


class Utils(commands.Cog):
    """Lệnh hữu dụng."""
    def __init__(self, bot: Furina):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if message.content == '<@1131530915223441468>':
            embed = FooterEmbed(
                description=(f"My Prefix is `{self.bot.prefixes.get(message.guild.id) or DEFAULT_PREFIX}`\n"
                              "### I also support slash commands \n-> Type `/` to see commands i can do!\n"
                              "### Or you can select one category below to see all the commands."), 
                color=Color.blue()
            )
            embed.set_author(
                name="Miss me that much?",
                icon_url="https://cdn.7tv.app/emote/01HHV72FBG000870SVK5KGTSJM/4x.png"
            )
            embed.timestamp = message.created_at
            view = SelectView().add_item(HelpSelect(self.bot))
            view.message = await message.channel.send(embed=embed, view=view, reference=message)

    @staticmethod
    def generate_random_number(min_num: int, max_num: int) -> int:
        random_number: int = -1
        for _ in range(100):
            random_number = random.randint(min_num, max_num)
        return random_number

    @commands.hybrid_command(name='ping', aliases=['test'], description="Đo ping và thông tin Node của bot.")
    async def ping_command(self, ctx: commands.Context):
        """Đo ping và thông tin Node của bot."""
        await ctx.defer()
        bot_latency = self.bot.latency
        voice_latency = ctx.guild.voice_client.ping if ctx.guild.voice_client else -1

        embed = AvatarEmbed(title="— Thành công!", user=ctx.author)
        embed.add_field(name="Độ trễ:", value=f"**Bot:** {bot_latency * 1000:.2f}ms\n**Voice:** {voice_latency}ms")

        for i, node in enumerate(wavelink.Pool.nodes, 1):
            node_ = wavelink.Pool.get_node(node)
            if node_.status == wavelink.NodeStatus.CONNECTED:
                node_status = ":white_check_mark:"
            elif node_.status == wavelink.NodeStatus.CONNECTING:
                node_status = ":arrows_clockwise:"
            else:
                node_status = ":negative_squared_cross_mark:"
            embed.add_field(name=f"Node {i}: {node_status}",
                            value="")
        await ctx.reply(embed=embed)

    @commands.command(name="prefix", description="Set a custom prefix")
    async def prefix_command(self, ctx: commands.Context, prefix: str):
        """Set a custom prefix or clear it with 'clear' or 'reset'"""
        async with aiosqlite.connect("config.db") as db:
            if prefix in ['clear', 'reset', 'default']:
                await db.execute(
                    f"""DELETE FROM custom_prefixes
                        WHERE guild_id = {ctx.guild.id}"""
                )
            else:
                await db.execute(
                    """INSERT INTO custom_prefixes ( guild_id, prefix )
                       VALUES ( ?, ? )
                       ON CONFLICT(guild_id) DO UPDATE SET
                       prefix = excluded.prefix""", (ctx.guild.id, prefix)
                )
            await db.commit()
        await self.bot.update_prefixes()
        await ctx.reply(
            embed=FooterEmbed(
                description=f"Prefix for this server has been changed to `{self.bot.prefixes.get(ctx.guild.id) or DEFAULT_PREFIX}`"
            )
        )

    @commands.command(name='source', aliases=['sources', 'src'], description="Mã nguồn")
    async def source_command(self, ctx: commands.Context):
        await ctx.reply("https://github.com/Th4nhZ/FurinaBot")

    @commands.hybrid_command(name='help', description="Hiển thị các lệnh của bot/xem chi tiết một lệnh nào đó.")
    async def help(self, ctx: commands.Context, command_name: Optional[str] = None):
        """
        Hiển thị các lệnh của bot hoặc xem chi tiết một lệnh nào đó

        Parameters
        -----------
        ctx
            commands.Context
        command_name: `str`
            Tên của lệnh cần xem chi tiết
        """
        if command_name is None:
            embed = discord.Embed(title="Help Command",
                                  description="Vui lòng chọn mục ở menu bên dưới.")
            view = TimeoutView().add_item(HelpSelect(self.bot))
            view.message = await ctx.send(embed=embed, view=view)

        else:
            command = self.bot.get_command(command_name)
            if command and command.hidden is False:
                usage = f"{ctx.prefix}{command.name}"
                for param in command.clean_params.values():
                    usage += f" {'<' if param.default else '['}{param.name}{'>' if param.default else ']'}"
                embed = discord.Embed()
                embed.title = f"Chi tiết lệnh {command.qualified_name}"
                embed.description = (f"- **__Tên:__** `{command.qualified_name}`\n"
                                     f"- **__Chi tiết:__** {command.description}\n"
                                     f"- **__Sử dụng:__** {usage}"
                                     )
                embed.set_footer(
                    text="Aliases: " + ", ".join(alias for alias in command.aliases)) if command.aliases else None
                await ctx.reply(embed=embed)
            else:
                raise commands.BadArgument("""Mình không nhận ra lệnh đó""")

    @commands.command(name='vps', description="Thông tin về máy ảo.")
    async def vps(self, ctx: commands.Context):
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

        embed = FooterEmbed(title="Thông tin về máy ảo")
        embed.add_field(name="Hệ điều hành", value=os_version)
        embed.add_field(
            name="CPU Usage",
            value=f"{cpu_percent}%",
            inline=False
        )
        embed.add_field(
            name="RAM Usage",
            value=f'- Tổng: {ram_total}GB\n'
                  f'- Đã dùng: {ram_used}GB\n'
                  f'- Đệm: {ram_cached}GB\n'
                  f'- Trống: {ram_available}GB',
            inline=False
        )
        embed.add_field(
            name="Disk Usage",
            value=f'- Tổng: {disk_total}GB\n'
                  f'- Đã dùng: {disk_used}GB\n'
                  f'- Trống: {disk_available}GB',
            inline=False
        )
        await ctx.reply(embed=embed)

    @commands.hybrid_command(name='userinfo', aliases=['uinfo', 'whois'], description="Xem thông tin của một ai đó.")
    @app_commands.describe(member="username, id người đó")
    async def user_info(self, ctx: commands.Context, member: Optional[discord.Member] = None) -> None:
        member = member or ctx.author
        embed = discord.Embed(title="— Thông tin người dùng", color=discord.Color.blue())
        embed.add_field(name="Tên hiển thị:", value=member.mention)
        embed.add_field(name="Username:", value=member)
        embed.add_field(name="ID:", value=member.id)
        embed.set_thumbnail(url=member.avatar.url)
        embed.add_field(name="Ngày tạo tài khoản:",
                        value="`  " + datetime.fromisoformat(str(member.created_at + timedelta(hours=7))).strftime(
                            "%H:%M:%S  \n %d/%m/%Y") + " `")
        embed.add_field(name="Ngày tham gia:",
                        value="`  " + datetime.fromisoformat(str(member.joined_at + timedelta(hours=7))).strftime(
                            "%H:%M:%S  \n %d/%m/%Y") + " `")
        status = str(member.status)
        if status == 'online':
            member_status = ":green_circle: Đang Online"
        elif status == 'offline':
            member_status = ":black_circle: Đã Offline"
        elif status == 'idle':
            member_status = ":yellow_circle: Đang treo máy"
        else:
            member_status = ":red_circle: Đừng làm phiền"
        embed.add_field(name="Trạng thái hoạt động: ", value=member_status)
        roles = [role for role in reversed(member.roles) if role.name != '@everyone']
        embed.add_field(name="Roles:", value=", ".join(role.mention for role in roles))
        if member.activity:
            embed.add_field(name="Trạng thái tùy chỉnh:",
                            value=f"{member.activity.emoji if member.activity.emoji else ''} **{str.capitalize(member.activity.type.name)}**: {member.activity.name}" if member.activity.name != None else "Không có")
        embed.set_footer(text="Coded by ThanhZ")
        embed.timestamp = ctx.message.created_at
        await ctx.reply(embed=embed)

    @commands.command(name='random',
                      aliases=['rand'],
                      description="Random số ngẫu nhiên.")
    async def random(self, ctx: commands.Context, number: Optional[int] = 1) -> None:
        embed = discord.Embed()
        if number == 1:
            rand_num = self.generate_random_number(0, 10)
        else:
            seq = ""
            for i in range(number):
                rand_num = self.generate_random_number(0, 10)
                seq += f"{rand_num} "
            embed.add_field(name="Lịch sử:", value=f"```\n{seq[:-1]}\n```")
        if rand_num < 4:
            embed.color = discord.Color.darker_gray()
            embed.set_footer(text="Bạn đen lắm.")
        elif 3 < rand_num < 8:
            embed.color = discord.Color.dark_purple()
            embed.set_footer(text="Vận may bình thường.")
        elif 7 < rand_num < 10:
            embed.color = discord.Color.pink()
            embed.set_footer(text="Khá may mắn.")
        else:
            embed.color = discord.Color.red()
            embed.set_footer(text="Hôm nay bạn rất may mắn.")
        embed.set_author(name=f"{ctx.author.display_name} đã thử vận may của mình {number} lần",
                         icon_url="https://cdn.7tv.app/emote/6175d52effc7244d797d15bf/4x.gif")
        embed.title = f"Con số may mắn là: {rand_num}"
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.command(name='dice',
                      aliases=['roll'],
                      description="Tung xúc xắc.")
    async def dice(self, ctx: commands.Context, number: Optional[int] = 1) -> None:
        embed = discord.Embed()
        if number == 1:
            rand_num = self.generate_random_number(1, 6)
        else:
            seq = ""
            for i in range(number):
                rand_num = self.generate_random_number(1, 6)
                seq += f"{rand_num} "
            embed.add_field(name="Lịch sử:", value=f"```\n{seq[:-1]}\n```")
        embed.set_author(name=f"{ctx.author.display_name} đã tung xúc xắc {number} lần",
                         icon_url="https://cdn.7tv.app/emote/6175d52effc7244d797d15bf/4x.gif")
        embed.title = f"Con số trên xúc xắc là: {rand_num}"
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @commands.command(name='flip',
                      aliases=['coin', 'coinflip'],
                      description="Tung đồng xu.")
    async def flip(self, ctx: commands.Context, number: Optional[int] = 1) -> None:
        embed = discord.Embed()
        if number == 1:
            for _ in range(100):
                rand_flip = random.choice(["Sấp", "Ngửa"])
        else:
            seq = ""
            for i in range(number):
                for i in range(100):
                    rand_flip = random.choice(["Sấp ", "Ngửa"])
                seq += f"{rand_flip[:-3]} "
            embed.add_field(name="Lịch sử:", value=f"```\n{seq[:-1]}\n```")
        embed.set_author(name=f"{ctx.author.display_name} đã tung một đồng xu {number} lần",
                         icon_url="https://cdn.7tv.app/emote/6175d52effc7244d797d15bf/4x.gif")
        embed.title = f"Mặt hiện tại của đồng xu là: {rand_flip}"
        await ctx.send(embed=embed)
        await ctx.message.delete()

    @staticmethod
    async def dictionary_call(word: str) -> PaginatedView:
        """
        Tạo API call đến dictionaryapi

        Parameters
        -----------
        `word: str`
            Từ cần tra từ điển.

        Returns
        -----------
        `PaginatedView`
            A view that contains list of embeds and navigate buttons
        """
        embeds: list[Embed] = []
        async with aiohttp.ClientSession() as cs:
            async with cs.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}") as response:
                if response.status == 404:
                    embed = FooterEmbed(
                        title=word.capitalize(),
                        description="No definitions found. API call returned 404."
                    )
                    return PaginatedView(timeout=300, embeds=[embed])
                data: list[dict] = eval(await response.text())

        embed = FooterEmbed(title=word.capitalize())

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
                embed = FooterEmbed(
                    title=word.capitalize(),
                    description=f"Pronunciation: `{phonetics}`"
                )
        return PaginatedView(timeout=300, embeds=embeds)

    @commands.hybrid_command(name='dictionary', aliases=['dict'], description="Tra từ điển một từ.")
    @app_commands.allowed_installs(guilds=True, users=True)
    async def dict_command(self, ctx: commands.Context, word: str):
        """
        Tra từ điển một từ.
        
        Parameters
        -----------
        ctx: `commands.Context`
            Context
        word: `str`
            Từ cần tra
        """
        view = await self.dictionary_call(word.split()[0])
        view.message = await ctx.reply(embed=view.embeds[0], view=view)


async def setup(bot: Furina):
    await bot.add_cog(Utils(bot))