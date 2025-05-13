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

import pathlib
from typing import TYPE_CHECKING

import asqlite
import enka
from discord.ext import commands

from core import FurinaCog, FurinaCtx

if TYPE_CHECKING:
    import discord

    from core import FurinaBot


class Gacha(FurinaCog):
    """Gacha Related Commands"""
    def __init__(self, bot: FurinaBot) -> None:
        super().__init__(bot)
        self.gi = enka.GenshinClient()
        self.hsr = enka.HSRClient()

    async def cog_load(self) -> None:
        self.pool = await asqlite.create_pool(pathlib.Path() / 'db' / 'gacha.db')
        await self.__create_gacha_tables()
        return await super().cog_load()

    async def __create_gacha_tables(self) -> None:
        async with self.pool.acquire() as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS gi_uid
                (
                    user_id INTEGER NOT NULL PRIMARY KEY,
                    uid TEXT NOT NULL
                )
                """)
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS hsr_uid
                (
                    user_id INTEGER NOT NULL PRIMARY KEY,
                    uid TEXT NOT NULL
                )
                """)

    @property
    def embed(self) -> discord.Embed:
        """Shortcut for FurinaBot.embed"""
        return self.bot.embed.set_footer(text="Coded by ThanhZ | Powered by Enka Network")

    @commands.hybrid_group(name='gi', description="Get user info", fallback='get')
    async def gi_group(self, ctx: FurinaCtx, uid: str | None = None) -> None:
        if uid is None:
            async with self.pool.acquire() as db:
                uid = await db.fetchone("SELECT uid FROM gi_uid WHERE user_id = ?", ctx.author.id)
                uid = uid[0] if uid else None
                if uid is None:
                    await ctx.reply(
                        "You have not set a UID yet! Use `/gi set <uid>` to set your UID"
                    )
                    return

        async with self.gi as api:
            response = await api.fetch_showcase(uid)
            p_info = response.player
        embed = self.embed
        embed.title = f"{p_info.nickname}"
        embed.set_author(name=uid, icon_url=p_info.profile_picture_icon.circle)
        embed.set_thumbnail(url=p_info.namecard.full)
        abyss = f"{p_info.abyss_floor}-{p_info.abyss_level} ({p_info.abyss_stars})"
        embed.description = (f"> {p_info.signature}\n"
                             f"**Adventure Rank:** `{p_info.level}`\n"
                             f"**World Level:** `{p_info.world_level}`\n"
                             f"**Achievements:** `{p_info.achievements}`\n"
                             f"**Abyss Floor:** `{abyss}`")
        await ctx.reply(embed=embed)

    @gi_group.command(name='set', description='Set your UID')
    async def set_uid_gi(self, ctx: FurinaCtx, *, uid: str) -> None:
        async with self.gi as api, self.pool.acquire() as db:
            try:
                await api.fetch_showcase(uid, info_only=True)
            except enka.errors.WrongUIDFormatError:
                await ctx.reply("Invalid UID!")
                return
            await db.execute("INSERT OR REPLACE INTO gi_uid (user_id, uid) VALUES (?, ?)",
                             ctx.author.id, 
                             uid)
        await ctx.reply("Your GI UID has been set to: " + uid)

    @commands.hybrid_group(name='hsr', description="Get HSR user info", fallback='get')
    async def hsr_group(self, ctx: FurinaCtx, uid: str | None = None) -> None:
        if not uid:
            async with self.pool.acquire() as db:
                uid = await db.fetchone("SELECT uid FROM hsr_uid WHERE user_id = ?", ctx.author.id)
                uid = uid[0] if uid else None
                if uid is None:
                    await ctx.reply(
                        "You have not set a UID yet! Use `/hsr set <uid>` to set your UID"
                    )
                    return

        async with self.hsr as api:
            response = await api.fetch_showcase(uid)
            p_info = response.player
            p_stats = p_info.stats
        embed = self.embed
        embed.title = f"{p_info.nickname}"
        embed.set_author(name=uid, icon_url=p_info.icon)
        embed.description = (f"> {p_info.signature}\n"
                             f"**Trailblaze Level:** `{p_info.level}`\n"
                             f"**Equilibrium Level:** `{p_info.equilibrium_level}`\n"
                             f"**Stats:**\n"
                             f">>> **Achievements**: `{p_stats.achievement_count}`\n"
                             f"**Characters**: `{p_stats.character_count}`\n"
                             f"**Lightcones**: `{p_stats.light_cone_count}`"
        )
        await ctx.reply(embed=embed)

    @hsr_group.command(name='set', description='Set your UID')
    async def set_uid_hsr(self, ctx: FurinaCtx, *, uid: str) -> None:
        async with self.hsr as api, self.pool.acquire() as db:
            try:
                await api.fetch_showcase(uid, info_only=True)
            except enka.errors.WrongUIDFormatError:
                await ctx.reply("Invalid UID!")
                return
            await db.execute("INSERT OR REPLACE INTO hsr_uid (user_id, uid) VALUES (?, ?)", 
                             ctx.author.id, 
                             uid)
        await ctx.reply("Your HSR UID has been set to: " + uid)


async def setup(bot: FurinaBot) -> None:
    await bot.add_cog(Gacha(bot))