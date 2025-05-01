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

from typing import List

from discord import ui, Button, Embed, Interaction, Message, User
from discord.ext.commands import CommandError, CooldownMapping


class UIElementOnCoolDownError(CommandError):
    def __init__(self, retry_after: float):
        self.retry_after = retry_after

class View(ui.View):
    """A View that auto disable children when timed out"""
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)
        self.message: Message
        self.cd = CooldownMapping.from_cooldown(rate=1, per=3, type=self.key)

    @staticmethod
    def key(interaction: Interaction) -> User:
        return interaction.user

    async def interaction_check(self, interaction: Interaction):
        retry_after = self.cd.update_rate_limit(interaction)
        if retry_after:
            raise UIElementOnCoolDownError(retry_after=retry_after)
        return True

    async def on_error(self, interaction: Interaction, error: Exception, item: ui.Item):
        if isinstance(error, UIElementOnCoolDownError):
            seconds = int(error.retry_after)
            unit = 'second' if seconds == 1 else 'seconds'
            await interaction.response.send_message(f"You are clicking too fast, try again in {seconds} {unit}!", ephemeral=True)
        else:
            await super().on_error(interaction, error, item)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.message.edit(view=self)


class PaginatedView(View):
    def __init__(self, *, timeout: float, embeds: List[Embed] | Embed):
        super().__init__(timeout=timeout)
        self.embeds = embeds if isinstance(embeds, List) else [embeds, ]
        self.page: int = 0
        if len(self.embeds) == 1:
            self.clear_items()

    @ui.button(label="<", disabled=True)
    async def left_button(self, interaction: Interaction, button: Button):
        self.page -= 1
        button.disabled = True if self.page == 0 else False
        self.right_button.disabled = False
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @ui.button(label=">")
    async def right_button(self, interaction: Interaction, button: Button):
        self.page += 1 if self.page <= len(self.embeds) - 1 else self.page
        button.disabled = True if self.page == len(self.embeds) - 1 else False
        self.left_button.disabled = False
        await interaction.response.edit_message(embed=self.embeds[self.page], view=self)


class LayoutView(ui.LayoutView):
    async def on_timeout(self) -> None:
        for child in self.walk_children():
            child.disabled = True
        await self.message.edit(view=self)

