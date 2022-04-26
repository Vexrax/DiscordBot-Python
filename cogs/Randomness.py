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


async def setup(client):
    await client.add_cog(Randomness(client))
