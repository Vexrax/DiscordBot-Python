import discord
from discord.ext import commands
import youtube_dl

class Music(commands.Cog):


    def __init__(self, client):
        self.client = client
        self.players = {}

    @commands.Cog.listener()
    async def on_ready(self):
        print("Music Command Ready")

    @commands.command()
    async def join(self, ctx):
        channel = ctx.author.voice.channel
        await channel.connect()

    @commands.command()
    async def leave(self, ctx):
        await ctx.voice_client.disconnect()

    @commands.command()
    async def play(self, ctx, url):
        # guild = ctx.message.guild
        # voice_client = guild.voice_client
        # player = await voice_client.create_ytdl_player(url)
        # self.players[guild.id] = player
        # player.start()
        await ctx.send("This command is WIP")

    # @commands.Cog.listener()
    # async def on_command_error(self, ctx, error):
    #     if isinstance(error, commands.MissingRequiredArgument):
    #         await ctx.send('Music command error')

def setup(client):
    client.add_cog(Music(client))