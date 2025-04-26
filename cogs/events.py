from __future__ import annotations

import traceback
from typing import TYPE_CHECKING

from discord import ui, Activity, ActivityType, DMChannel, Message, Member
from discord.ext import commands
from wavelink import Player, Playable, TrackStartEventPayload, TrackEndEventPayload

from furina import FurinaCtx, FurinaCog
from settings import MUSIC_CHANNEL, ACTIVITY_NAME, CROSS


if TYPE_CHECKING:
    from furina import FurinaBot


class BotEvents(FurinaCog):
    async def update_activity(self, state: str = "N̸o̸t̸h̸i̸n̸g̸") -> None:
        """
        Update the bot's activity to the playing track.

        Parameters
        -----------
        bot: `commands.Bot`
            bot
        state: `str`
            Track name
        """
        await self.bot.change_presence(activity=Activity(type=ActivityType.playing, name=ACTIVITY_NAME, state=f"Playing: {state}"))

    @commands.Cog.listener()
    async def on_message(self, message: Message) -> None:
        if message.author.bot:
            return

        # Processing DMs
        if isinstance(message.channel, DMChannel):
            await message.forward(self.bot.get_user(self.bot.owner_id))

    @commands.Cog.listener()
    async def on_command_error(self, ctx: FurinaCtx, error: commands.errors.CommandError) -> None:
        err: str = CROSS
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            err += f" **Missing required argument:** `{error.param.name}`"
        else:
            err += f" **{error}**"
        view = ui.LayoutView().add_item(ui.Container(ui.TextDisplay(err)))
        await ctx.reply(view=view, ephemeral=True, delete_after=60)

        traceback.print_exception(error)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: Member, before, after) -> None:
        # Change activity when bot leave voice channel
        if member == self.bot.user and not after.channel:
            await self.update_activity()

        # Leave if the bot is the last one in the channel
        if before.channel and not after.channel:
            if len(before.channel.members) == 1 and before.channel.members[0] == self.bot.user:
                await member.guild.voice_client.disconnect(force=True)
                channel = self.bot.get_channel(MUSIC_CHANNEL)
                embed = self.bot.embed
                embed.title = "I am not afraid of ghost i swear :fearful:"
                embed.set_image(url="https://media1.tenor.com/m/Cbwh3gVO4KAAAAAC/genshin-impact-furina.gif")
                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: TrackEndEventPayload) -> None:
        """Update activity if the queue is empty"""
        player: Player = payload.player
        if player.queue.is_empty:
            await self.update_activity()

    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: TrackStartEventPayload) -> None:
        """Update activity when a track starts playing"""
        track: Playable = payload.track
        await self.update_activity(track.title)


async def setup(bot: FurinaBot) -> None:
    await bot.add_cog(BotEvents(bot))

