import asyncio

import discord
import random
from discord.ext import commands
import utils.Util as botUtil
import utils.VoteUtil as voteUtil

votesRequiredToPass = 300
textMuteRoleName = "TextMute"
timeToStayTextMuted = 120


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

    @commands.command()
    async def voteTextMute(self, ctx):

        if not await self.canUseCommand(ctx):
            return

        user = ctx.message.mentions[0]
        target = user.mention
        textMuteRole = discord.utils.get(ctx.guild.roles, name=textMuteRoleName)

        voteMessage = f"Vote has been started to text mute the user {target} for {timeToStayTextMuted} seconds. react with 👍 or 👎 to vote on if this user should be text muted"
        message = await voteUtil.setupVote(ctx, voteMessage, voteUtil.timeforvote)
        if await voteUtil.hasVotePassed(ctx, ctx.channel, message.id, votesRequiredToPass):
            await user.add_roles(textMuteRole)
            await ctx.send(f"Vote Passed, {target} has been text muted for {timeToStayTextMuted} seconds")
        else:
            await ctx.send(f"Vote Failed, you could not text mute {target}!")
        await botUtil.sendDemocracy(ctx)
        await asyncio.sleep(timeToStayTextMuted)
        await user.remove_roles(textMuteRole)

    async def canUseCommand(self, ctx):

        if len(ctx.message.mentions) < 1:
            await ctx.send("User Specified counldn't be found, please make sure you have correctly @'d a valid user")
            return False

        return True

async def handleOnMessage(message):
    textMuteRole = discord.utils.get(message.guild.roles, name=textMuteRoleName)

    if hasattr(message.author, "roles") and len(message.author.roles) > 0 and textMuteRole in message.author.roles:
        await message.delete()

async def setup(client):
    await client.add_cog(Mute(client))