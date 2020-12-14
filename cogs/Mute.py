import discord
import random
from discord.ext import commands
import utils.Util as botUtil
import utils.VoteUtil as voteUtil

votesRequiredToPass = 300

class Mute(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Mute Command Ready")

    @commands.command()
    async def voteMute(self, ctx):

        if not await self.canUseCommand(ctx):
            return

        user = ctx.message.mentions[0]
        target = user.mention

        voteMessage = f"Vote has been started to mute the user {target} react with 👍 or 👎 to vote on if this user should be muted"
        message = await voteUtil.setupVote(ctx, voteMessage, voteUtil.timeforvote)
        if await voteUtil.hasVotePassed(ctx, ctx.channel, message.id, votesRequiredToPass):
            await user.edit(mute=True)
            await ctx.send(f"Vote Passed, {target} has been muted. You may vote to unmute him with voteUnmute!")
        else:
            await ctx.send(f"Vote Failed, you could not silence {target}!")
        await botUtil.sendDemocracy(ctx)

    @commands.command()
    async def voteUnmute(self, ctx):

        if not await self.canUseCommand(ctx):
            return

        user = ctx.message.mentions[0]
        target = user.mention

        voteMessage = f"Vote has been started to unmute the user {target} react with 👍 or 👎 to vote on if this user should be unmuted"
        message = await voteUtil.setupVote(ctx, voteMessage, voteUtil.timeforvote)
        if await voteUtil.hasVotePassed(ctx, ctx.channel, message.id, votesRequiredToPass):
            await user.edit(mute=False)
            await ctx.send(f"Vote Passed, {target} has been unmuted. You may vote to unmute him with voteUnmute!")
        else:
            await ctx.send(f"Vote Failed, you could not unsilence {target}!")
        await botUtil.sendDemocracy(ctx)

    async def canUseCommand(self, ctx):

        if len(ctx.message.mentions) < 1:
            await ctx.send("User Specified counldn't be found, please make sure you have correctly @'d a valid user")
            return False

        return True

def setup(client):
    client.add_cog(Mute(client))