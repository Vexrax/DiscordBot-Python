import discord
import random
from discord.ext import commands

class EightBall(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("8Ball Command Ready")

    @commands.command(aliases=["8ball"])
    async def _8ball(self, ctx, *, question):
        responses = ["As I see it, yes.",
                     "Ask again later",
                     "Better not tell you now.",
                     "Cannot predict now.",
                     "Concentrate and ask again.",
                     "Don't count on it.",
                     "It is certain.",
                     "It is decidedly so.",
                     "Yes – definitely",
                     " Without a doubt.",
                     " Outlook good.",
                     "Outlook not so good."]
        await ctx.send(f'Question {question}\n Answer: {random.choice(responses)}')

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send('Please ask a question or say something')

def setup(client):
    client.add_cog(EightBall(client))