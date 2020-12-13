import discord
import random
from discord.ext import commands
import utils.Util as botUtil

adminRoleName = "Admin"

class Election(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Election Command Ready")

    @commands.command()
    async def startElectionFor(self, ctx):

        if not await self.canUseCommand(ctx):
            return

        adminRole = discord.utils.get(ctx.guild.roles, name=adminRoleName)

        user = ctx.message.mentions[0]
        nomination = user.mention

        if adminRole in user.roles:
            await ctx.send(f"{nomination} is already an  {adminRole.name}")
            return

        voteMessage = f"{nomination} has been nominated to become an  {adminRole.name}, react with 👍 or 👎 to vote on if this user should be promoted to  {adminRole.name}"
        message = await botUtil.setupVote(ctx, voteMessage)


        if await botUtil.hasVotePassed(ctx, ctx.channel, message.id, botUtil.votesrequired):
            await user.add_roles(adminRole)
            await ctx.send(f"{nomination} has been received enough support and is now an {adminRole.name}")
        else:
            await ctx.send(f"{nomination} could not receive enough support and didnt get elected to {adminRole.name}")

        await botUtil.sendDemocracy(ctx)

        return

    @commands.command()
    async def disposeOfAdmin(self, ctx):

        if not await self.canUseCommand(ctx):
            return

        adminRole = discord.utils.get(ctx.guild.roles, name=adminRoleName)

        user = ctx.message.mentions[0]
        nomination = user.mention

        if adminRole not in user.roles:
            await ctx.send(f"{nomination} does not have an {adminRole.name} rank, you cannot dipose of them")
            return

        voteMessage = f"{nomination} has been nominated to be disposed and lose their {adminRole.name} rank, react with 👍 or 👎 to vote on if this user should be disposed"
        message = await botUtil.setupVote(ctx, voteMessage)

        if await botUtil.hasVotePassed(ctx, ctx.channel, message.id, botUtil.votesrequired):
            await user.remove_roles(adminRole)
            await ctx.send(f"{nomination} has received enough votes to be disposed, {nomination} has lost thier  {adminRole.name} rank")
        else:
            await ctx.send(f"Not enough users wanted to dispose of {nomination}. {nomination} will retain their  {adminRole.name} rank")

        await botUtil.sendDemocracy(ctx)
        return

    async def canUseCommand(self, ctx):

        if len(ctx.message.mentions) < 1:
            await ctx.send("User Specified counldn't be found, please make sure you have correctly @'d a valid user")
            return False

        if botUtil.isSkynet(ctx.message.mentions[0].id):
            await ctx.send("You cannot touch the system")
            return False

        return True


def setup(client):
    client.add_cog(Election(client))