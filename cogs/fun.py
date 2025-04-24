from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING

import numpy as np
from discord import app_commands, ui, Interaction, Message
from discord.ext import commands

from furina import FurinaCog, FurinaCtx

if TYPE_CHECKING:
    from furina import FurinaBot


class Fun(FurinaCog):
    """Funni Commands haha XD"""
    def __init__(self, bot: FurinaBot) -> None:
        super().__init__(bot)
        self.ctx_menu_liemeter = app_commands.ContextMenu(name="Lie Detector", callback=self.lie_detector)
        self.bot.tree.add_command(self.ctx_menu_liemeter)

    async def cog_unload(self):
        self.bot.tree.remove_command(self.ctx_menu_liemeter.name, type=self.ctx_menu_liemeter.type)
    
    async def lie_detector(self, interaction: Interaction, message: Message):
        if message.author.id == self.bot.user.id:
            await interaction.response.send_message("I always tell the truth")
            return
        if np.random.random() < 0.5:
            await interaction.response.send_message("This message is verified to be the truth")
        else:
            await interaction.response.send_message("https://tenor.com/kXIbVjdMB8x.gif")

    @staticmethod
    def generate_random_number(min_num: int, max_num: int, number: int = 1) -> List[int]:
        return np.random.randint(min_num, max_num + 1, 100*number).tolist()

    @commands.command(name='fortune', aliases=['lucky', 'slip', 'fortuneslip'], description="Draw a fortune slip")
    async def fortune_slip(self, ctx: FurinaCtx, number: Optional[int] = 1) -> None:
        fortunes = [
            "Great Fortune", 
            "Good Fortune", 
            "Modest Fortune", 
            "Rising Fortune", 
            "Misfortune", 
            "Great Misfortune"
        ]
        fortune_yap = [
            [
"""
The message you've been waiting for will arrive without delay.
A mistake from the past becomes your hidden strength.
You'll meet someone who reminds you who you really are.
Even rushed choices will land on steady ground.
Today flows like a river—let it carry you.

Your lucky object for the day: [Worn Leather Wallet]
[It's held your hopes and hardships—now it holds your luck.]
Trust what's already in your pocket.
""",
"""
The thing you almost gave up on? It's about to surprise you.
Unseen effort will finally get its spotlight.
A conversation will shift something deep inside you.
Today, your presence carries more power than you know.
Everything's moving in your favor—even the little things.

Your lucky object for the day: [Ballpoint Pen]
[Used to sign forms, letters, destinies.]
Write something down today—it matters more than you think.
""",
"""
That idea you brushed off? Try it again.
Even closed doors creak open with the right timing.
You'll notice signs you once overlooked.
A small risk will return a big reward.
Today, you're in rhythm with the world.

Your lucky object for the day: [Set of Keys]
[They open more than just locks.]
Keep them close—you're about to need them.
""",
"""
You'll bump into joy when you're not looking.
The thing you dread will turn out way easier than expected.
Someone's been rooting for you quietly—today, you'll know who.
Your timing is sharper than ever.
Things are about to click into place.

Your lucky object for the day: [Travel Mug]
[It holds warmth through movement.]
Stay fueled—both literally and figuratively.
""",
"""
Today, something old will feel new again.
A forgotten skill or hobby will call to you.
Luck will show up disguised as a minor inconvenience.
You're walking into a stretch of clarity.
Even hesitation will take you somewhere meaningful.

Your lucky object for the day: [Wristwatch]
[It ticks with every second you own.]
Don't waste time doubting yourself.
"""],
            [
"""
You'll notice progress where there used to be only effort.
Something small will go better than planned.
An unexpected compliment will stick with you.
Today brings steady steps, not giant leaps—and that's enough.

Your lucky object for the day: [Phone Charger]
[It brings things back to life quietly.]
Keep your energy topped up—momentum needs maintenance.
""",
"""
You'll make someone's day without realizing it.
Things won't go perfectly, but they'll go right.
You'll dodge a problem just by being yourself.
It's a good day to ask, even if you're not sure of the answer.

Your lucky object for the day: [Sticky Note]
[It holds reminders the brain forgets.]
Write it down—clarity hides in lists.
""",
"""
A boring task will bring an oddly satisfying reward.
Someone will thank you for something you forgot you did.
You'll stumble into a small piece of peace.
Today is built for quiet wins—don't ignore them.

Your lucky object for the day: [Reusable Water Bottle]
[Always full if you remember to refill.]
Take care of your basics—they carry you farther than luck.
""",
"""
Plans may shift, but something better comes through the cracks.
A mild inconvenience saves you from a worse one.
Someone's words will stick with you in a helpful way.
You're not behind—you're exactly where you're supposed to pivot.

Your lucky object for the day: [Umbrella]
[It doesn't stop the rain, but it helps you face it.]
Be ready, not worried.
""",
"""
You'll finally understand something that's been bugging you.
An old message or photo will remind you how far you've come.
Today has no sharp turns—just gentle curves in the right direction.
It's a day to appreciate what is, not just chase what's next.

Your lucky object for the day: [Pair of Headphones]
[They help you tune in or tune out, depending on what you need.]
Listen carefully—to music, to people, to yourself.
"""],
            [
"""
You'll avoid an awkward moment without realizing it.
A tiny choice today might save you some hassle later.
Your effort won't wow anyone—but it'll get the job done.
Don't expect fireworks, but don't expect rain either.

Your lucky object for the day: [Binder Clip]
[Small, strong, and underrated.]
Keep it all together, even if it's just barely.
""",
"""
You'll remember something just in time.
An inconvenience will end quicker than expected.
You might not win, but you'll place higher than usual.
Today's more about not losing than it is about winning.

Your lucky object for the day: [Bus Ticket]
[It only goes one way—but that might be enough.]
Keep moving, even slowly.
""",
"""
The thing you were worried about? Turns out to be just meh.
You won't be the star today, but you'll still be solid backup.
You'll have one small victory to quietly celebrate.
It's a good day to blend in and not mess things up.

Your lucky object for the day: [Pencil]
[Easy to sharpen, even easier to erase.]
Mistakes today won't stick if you fix them fast.
""",
"""
Someone will almost annoy you, but you'll let it slide.
You won't finish everything, but you'll finish the part that matters.
A half-hearted effort might still be enough today.
Your luck's not loud—but it's not leaving either.

Your lucky object for the day: [Roll of Tape]
[Holds things together temporarily, but surprisingly well.]
Patch things, even if it's not perfect.
""",
"""
Your timing won't be great—but it won't be terrible either.
Someone might flake on you, but you'll kind of be glad.
You'll be mildly surprised in a good way—twice.
Today's main win: nothing major goes wrong.

Your lucky object for the day: [Coin in Your Pocket]
[Not enough to buy much, but better than nothing.]
Carry a little luck—just in case.
"""],
            [
"""
Something you've been working on will finally start showing signs of life.
A chance meeting will plant the seed for something bigger.
You'll feel more ready today, even if nothing's changed.
Momentum is building—just keep walking forward.

Your lucky object for the day: [Elevator Button]
[You're not at the top yet, but the floor's rising.]
Press forward—literally or not.
""",
"""
Someone will take notice of what you're doing—quietly, but it counts.
An opportunity will open, even if you don't take it right away.
Confidence might arrive before the results do.
Today is all about potential—it's okay if it's not flashy yet.

Your lucky object for the day: [Unopened Letter]
[What's inside hasn't changed—but your readiness to read it might have.]
Keep your eyes peeled for signs.
""",
"""
You'll solve a small problem that's been lowkey bothering you.
Plans will come together, just enough to feel real.
Support you didn't expect will show up in small gestures.
You're not there yet—but you can see the path now.

Your lucky object for the day: [Train Schedule]
[Everything's in motion—you just need the right stop.]
Patience is part of progress.
""",
"""
A slow start turns into something surprisingly productive.
You'll impress someone by accident.
Today brings a little clarity about what's next.
There's more ahead, and for once, that feels exciting.

Your lucky object for the day: [New Pair of Socks]
[Not glamorous, but they get you where you're going.]
Comfort can be momentum too.
""",
"""
You'll find a reason to be hopeful without trying too hard.
Something small today will snowball in a good way later.
The vibes aren't perfect—but they're definitely improving.
It's a good day to prep for what you want to happen.

Your lucky object for the day: [Blank Notebook]
[Every line you fill moves you forward.]
Start something—even if it's just the outline.
"""],
            [
"""
A simple task might turn oddly complicated.
Someone may misunderstand you, even if you explain.
You'll get what you asked for—but not how you wanted it.
Today's best move might be staying out of the way.

Your unlucky object for the day: [Slippery Soap Bar]
[Hard to hold onto, and vanishes faster than expected.]
Let go of what's too tricky to grip today.
""",
"""
You might say the right thing at the wrong time.
Plans will shift, but not in your favor.
Patience will be tested—possibly more than once.
Take it slow. Rushing will only make it worse.

Your unlucky object for the day: [Overripe Banana]
[Looks okay till you pick it up.]
Trust your gut when something feels "off."
""",
"""
A small mistake might get noticed more than it should.
You'll feel slightly offbeat, like everyone's on a different rhythm.
Not everything will go wrong—but enough to be annoying.
Try not to force anything today—it'll only push back.

Your unlucky object for the day: [Leaky Pen]
[It works... until it ruins your shirt.]
Watch out for messes you didn't plan on.
""",
"""
Someone might flake, and it'll throw your timing.
You'll need a backup plan—maybe even a backup for that.
Expect delays, distractions, and a mild existential sigh.
You'll get through it—but it won't be fun.

Your unlucky object for the day: [Empty Coffee Cup]
[All the promise, none of the energy.]
Rest, don't reach—you might knock something over.
""",
"""
You'll feel out of sync with everything.
What should work... won't.
You might lose something small, but inconvenient.
Today's goal? Survive it with your sanity intact.

Your unlucky object for the day: [Dead Battery]
[No juice, no spark, just frustration.]
Charge yourself before you try fixing anything else.
"""],
            [
"""
What can go wrong might go wrong—twice.
A small slip will spiral harder than expected.
Even silence will feel loud today.
This is not the day to test fate.

Your cursed object for the day: [Cracked Mirror]
[Shows you the truth, but distorts it just enough to sting.]
Avoid reflections—they won't help.
""",
"""
You'll feel misunderstood, even by yourself.
Things will break—physically or emotionally, hard to say.
Help will be just out of reach, timing just a little too late.
Today's lesson: survival, not success.

Your cursed object for the day: [Offline Router]
[All the connections, none of the function.]
Don't rely on external signals.
""",
"""
A moment of confidence may lead straight to embarrassment.
Warnings will be ignored. You might be the one ignoring them.
You'll run out—of time, energy, patience.
It's not rock bottom, but the ground's getting closer.

Your cursed object for the day: [Unzipped Backpack]
[Everything feels fine—until it's all gone.]
Double-check what you're carrying.
""",
"""
Someone will take something the wrong way—and it'll snowball.
A well-meant action might blow up in your face.
You'll question if today even happened right.
Avoid confrontation. Even shadows feel sharp.

Your cursed object for the day: [Microwave That Beeps Too Loud]
[Can't even warm things up without chaos.]
Let things cool. Literally and emotionally.
""",
"""
You'll make the effort, and still get the worst seat.
Support will vanish right when you need it.
Luck's on vacation, and karma's not picking up.
All you can do is not make it worse.

Your cursed object for the day: [Wobbly Chair]
[Looks stable until you sit down.]
Check before you trust anything today.
"""]
        ]
        if number == 1 or number not in range(1, 10_000):
            fortune = np.random.choice(range(len(fortunes)), size=100)[-1]
            header=f"{ctx.author.mention} thought very hard before drawing a fortune slip"
        else:
            fortune = np.random.choice(range(len(fortunes)), size=100*number)[-1]
            header=f"{ctx.author.mention} thought {number} times before drawing a fortune slip"
        yap = fortune_yap[fortune][np.random.choice(range(len(fortune_yap[fortune])), size=100)[-1]]
        fortune_section = ui.Section(
            ui.TextDisplay(header),
            ui.TextDisplay(f"## {fortunes[fortune]}"),
            ui.TextDisplay(yap),
            accessory=ui.Thumbnail("https://static.wikia.nocookie.net/gensin-impact/images/b/b0/Item_Fortune_Slip_Opened.png/revision/latest?cb=20210725221204")
        )
        container = ui.Container(
            fortune_section,
            ui.TextDisplay("-# This is just for fun, take it as a grain of salt | Coded by ThanhZ"),
        )
        view = ui.LayoutView(timeout=1).add_item(container)
        await ctx.send(view=view)

    @commands.command(name='dice', aliases=['roll'], description="Roll a dice 6")
    async def dice(self, ctx: FurinaCtx, number: Optional[int] = 1) -> None:
        embed = self.bot.embed
        if number == 1 or number not in range(1, 1000):
            rand_num = self.generate_random_number(1, 6)[-1]
            embed.set_author(name=f"{ctx.author.display_name} rolled a dice",
                            icon_url="https://cdn.7tv.app/emote/6175d52effc7244d797d15bf/4x.gif")
        else:
            seq = self.generate_random_number(1, 6, number)
            seq = [str(seq_) for seq_ in seq]
            rand_num = seq[-1]
            embed.add_field(name="History:", value=f"```\n{' '.join(seq[:500]) + ('...' if len(seq) > 500 else '')}\n```")
            embed.set_author(name=f"{ctx.author.display_name} rolled a dice {number} times",
                            icon_url="https://cdn.7tv.app/emote/6175d52effc7244d797d15bf/4x.gif")
        embed.title = f"The current number is: {rand_num}"
        await ctx.send(embed=embed)

    @commands.command(name='flip', aliases=['coin', 'coinflip'], description="Flip a coin")
    async def flip(self, ctx: FurinaCtx, number: Optional[int] = 1) -> None:
        embed = self.bot.embed
        if number == 1 or number not in range(1, 1000):
            rand_flip: List[str] = np.random.choice(["Head", "Tail"], size=100).tolist()[-1]
            embed.set_author(name=f"{ctx.author.display_name} flipped a coin",
                            icon_url="https://cdn.7tv.app/emote/6175d52effc7244d797d15bf/4x.gif")
        else:
            seq: List[str] = np.random.choice(["Head", "Tail"], size=100*number).tolist()
            rand_flip = seq[-1]
            seq = [seq_[0] for seq_ in seq]
            embed.add_field(name="History:", value=f"```\n{''.join(seq[:500]) + ('...' if len(seq) > 500 else '')}\n```")
            embed.set_author(name=f"{ctx.author.display_name} flipped a coin {number} times",
                            icon_url="https://cdn.7tv.app/emote/6175d52effc7244d797d15bf/4x.gif")
        embed.title = f"{rand_flip}"
        await ctx.send(embed=embed)

    @commands.command(name='8ball', description="Ask the magic 8 ball")
    async def magic_eight_ball(self, ctx: FurinaCtx, *, question: str) -> None:
        answers: List[str] = [
            "It is certain",
            "It is decidedly so",
            "Without a doubt",
            "Yes - definitely",
            "You may rely on it",
            "As I see it, yes",
            "Most likely",
            "Outlook good",
            "Yes",
            "Signs point to yes",
            "Don't count on it",
            "My reply is no",
            "My sources say no",
            "Outlook not so good",
            "Very doubtful",
            "Reply hazy, try again",
            "Ask again later",
            "Better not tell you now",
            "Cannot predict now",
            "Concentrate and ask again"]
        embed = self.bot.embed
        embed.set_author(name=f"{ctx.author.display_name} asked the magic 8 ball", 
                         icon_url=r"https://th.bing.com/th/id/R.94318dc029cf3858ebbd4a5bd95617d9?rik=%2bjjVGtbqXgWhQA&pid=ImgRaw&r=0")
        embed.description = f"> {question}\n- **Magic 8 Ball:** `{np.random.choice(answers)}`"
        await ctx.send(embed=embed)


async def setup(bot: FurinaBot) -> None:
    await bot.add_cog(Fun(bot))

