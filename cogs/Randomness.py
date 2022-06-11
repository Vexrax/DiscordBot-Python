import random

from discord.ext import commands


class Randomness(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Randomness Command Ready")

    @commands.command()
    async def flipcoin(self, ctx):
        await ctx.send(f'Coin landed on {random.choice(["Heads", "Tails"])}')

    @commands.command()
    async def rolldice(self, ctx):
        await ctx.send(f'Dice rolled a {random.randint(1, 6)}')

    @commands.command()
    async def mentalhelp(self, ctx):
        target = ""
        if len(ctx.message.mentions) != 0:
            user = ctx.message.mentions[0]
            target = user.mention
        await ctx.send(f'https://www.google.com/search?client=firefox-b-1-d&q=mental+hospitals+near+me+ {target}')

async def setup(client):
    await client.add_cog(Randomness(client))
