import discord, platform
from discord import Intents, Activity, ActivityType, Color, Message
from discord.ext import commands
from discord.ext.commands import Bot, when_mentioned_or, errors


from settings import *
from _extensions.utils import HelpSelect
from _extensions.music import update_activity
from _classes.embeds import FooterEmbed, ErrorEmbed
from _classes.views import SelectView


class Furina(Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix     = when_mentioned_or(PREFIX),
            strip_after_prefix = True,
            intents            = Intents.all(),
            owner_id           = OWNER_ID,
            help_command       = None,
            activity           = Activity(type=ActivityType.playing,
                                          name=ACTIVITY_NAME,
                                          state="Playing: N̸o̸t̸h̸i̸n̸g̸")
        )

    async def on_ready(self) -> None:
        print(PRFX + " Đã đăng nhập bằng " + Fore.BLUE + self.user.name)
        print(PRFX + " Discordpy version " + Fore.BLUE + discord.__version__)
        print(PRFX + " Python version " + Fore.BLUE + str(platform.python_version()))

        channel = self.get_channel(DEBUG_CHANNEL)
        embed = FooterEmbed(title="Bot hoàn tất khởi động và sẵn sàng nhận lệnh!")
        await channel.send(embed=embed)

    async def setup_hook(self) -> None:
        for filename in os.listdir("./_extensions"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f"_extensions.{filename[:-3]}")
                    print(PRFX + " Đã load extension: " + Fore.BLUE + str(filename[:-3]))
                except Exception as e:
                    print(PRFX + " Lỗi khi load extension " + Fore.BLUE + str(filename[:-3]) + f"{e}")

    async def on_command_error(self, ctx: commands.Context, error: errors.CommandError) -> None:
        embed = ErrorEmbed()
        if isinstance(error, commands.CommandNotFound):
            embed.description = f"Không tìm thấy lệnh `{ctx.message.content.split()[0]}`"
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.description = f"Lệnh của bạn thiếu phần: `{error.param.name}`"
        else:
            embed.description = f"{error}"
        await ctx.reply(embed=embed, ephemeral=True, delete_after=60)

    async def on_message(self, message: Message, /) -> None:
        # Xử lý tin nhắn riêng
        if isinstance(message.channel, discord.DMChannel):
            if message.author != self.user and message.author.id != self.owner_id:
                owner = self.get_user(self.owner_id)
                if not owner:
                    owner = await self.fetch_user(self.owner_id)
                embed = FooterEmbed(
                    title=f"{message.author} ({message.author.id}) đã gửi một tin nhắn",
                    description="`" + message.content + "`" if message.content else None
                )
                embed.timestamp = message.created_at
                await owner.send(embed=embed)
                if message.attachments:
                    for attachment in message.attachments:
                        await owner.send(attachment.url)

        # Xử lý khi được ping
        if message.content == '<@1131530915223441468>':
            embed = FooterEmbed(
                title=MENTIONED_TITLE,
                description=MENTIONED_DESC,
                color=Color.blue()
            )
            embed.timestamp = message.created_at
            view = SelectView().add_item(HelpSelect(self))
            view.message = await message.channel.send(embed=embed, view=view)

        # Xử lý lệnh
        await self.process_commands(message)

    async def on_voice_state_update(self, member: discord.Member, before, after):
        player_channel = before.channel
        if player_channel and not after.channel:
            if len(player_channel.members) == 1 and player_channel.members[0] == self.user:
                await member.guild.voice_client.disconnect(force=True)
                channel = self.get_channel(MUSIC_CHANNEL)
                embed = FooterEmbed(title="Đừng bỏ mình một mình trong kênh, mình sợ :fearful:")
                embed.set_image(url="https://media1.tenor.com/m/Cbwh3gVO4KAAAAAC/genshin-impact-furina.gif")
                await channel.send(embed=embed)
                await update_activity(self)