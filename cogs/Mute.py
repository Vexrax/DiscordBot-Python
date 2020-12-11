import discord
import random
from discord.ext import commands
import utils.Util as botUtil

class Mute(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Mute Command Ready")

    @commands.command()
    async def voteMute(self, ctx, *, user):

        if self.isAMention(user):
            await ctx.send("User Specified counldn't be found, please make sure you have correctly @'d a valid user")
            return

        user = await ctx.guild.fetch_member(user[3:-1])
        target = user.mention

        voteMessage = f"Vote has been started to mute the user {target} react with 👍 or 👎 to vote on if this user should be muted"
        message = await botUtil.setupVote(ctx, voteMessage)
        if await botUtil.hasVotePassed(ctx, ctx.channel, message.id, botUtil.votesrequired):
            await user.edit(mute=True)
            await ctx.send(f"Vote Passed, {target} has been muted. You may vote to unmute him with voteUnmute!")
        else:
            await ctx.send(f"Vote Failed, you could not silence {target}!")
        await self.sendDemocracy(ctx)

    @commands.command()
    async def voteUnmute(self, ctx, *, user):

        if self.isAMention(user):
            await ctx.send("User Specified counldn't be found, please make sure you have correctly @'d a valid user")
            return

        user = await ctx.guild.fetch_member(user[3:-1])
        target = user.mention

        voteMessage = f"Vote has been started to unmute the user {target} react with 👍 or 👎 to vote on if this user should be unmuted"
        message = await botUtil.setupVote(ctx, voteMessage)
        if await botUtil.hasVotePassed(ctx, ctx.channel, message.id, botUtil.votesrequired):
            await user.edit(mute=False)
            await ctx.send(f"Vote Passed, {target} has been unmuted. You may vote to unmute him with voteUnmute!")
        else:
            await ctx.send(f"Vote Failed, you could not unsilence {target}!")
        await self.sendDemocracy(ctx)

    async def sendDemocracy(self, ctx):
        await ctx.send("https://i.imgur.com/z9gqMMw.gif")

    def isAMention(self, user):
        return not user.startswith('<@!') and not user[-1] == '>'

def setup(client):
    client.add_cog(Mute(client))