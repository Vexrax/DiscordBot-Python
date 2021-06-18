from discord.ext import commands

from utils.EmbedBuilder import generateLeaderboardEmbed


class DiscordStats(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("DiscordStats Command Ready")

    @commands.cooldown(1, 6000, commands.BucketType.guild)
    @commands.command()
    async def mostMessages(self, ctx):
        messageDict = {}

        await ctx.send("Crunching the numbers, this will take some time!")

        for channel in ctx.guild.channels:
            if channel.type.name == "text":
                async for message in channel.history(limit=40000):
                    if message.author.name + message.author.discriminator in messageDict:
                        messageDict[message.author.name + message.author.discriminator] += 1
                    else:
                        messageDict[message.author.name + message.author.discriminator] = 1

        x = sorted(messageDict.items(), key=lambda p: p[1], reverse=True)
        embed = generateLeaderboardEmbed(x, "Most Messages", "Here's who uses the server the most", 9)
        await ctx.send(embed=embed)
        return

    @commands.command()
    async def earliestJoin(self, ctx):

        joinDict = {}
        for member in ctx.guild.members:
            joinDict[member.name + member.discriminator] = member.joined_at

        x = sorted(joinDict.items(), key=lambda p: p[1])
        embed = generateLeaderboardEmbed(x, "Oldest Members:", "Here are the server boomers", 9)
        await ctx.send(embed=embed)
        return

def setup(client):
    client.add_cog(DiscordStats(client))