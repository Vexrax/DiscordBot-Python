import discord
from discord.ext import commands
from discord.ext import tasks
from discord.ui import Button, View

namingConvention = "sn-private-"


class PrivateChannel(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Private Channel Command Ready")
        self.cleanupUnusedPrivateChannels.start()

    @commands.command()
    async def privateChannel(self, ctx):
        mentions = ctx.message.mentions
        if len(mentions) == 0:
            await ctx.send('You cannot make a private channel for just yourself. Get some friends!')
            return

        category = discord.utils.get(ctx.guild.categories, name="General")

        voiceChannelName = f'{namingConvention}{ctx.message.author.name}'

        voiceChannel = await ctx.guild.create_voice_channel(voiceChannelName,
                                                            category=category,
                                                            reason="Skynet Create Voice Channel",
                                                            user_limit=len(mentions) + 1)

        # Allow person in by their Id
        await voiceChannel.set_permissions(ctx.message.author, connect=True, view_channel=True)
        for member in mentions:
            await voiceChannel.set_permissions(member, connect=True, view_channel=True)

        # Setup secondary Perms
        adminRole = discord.utils.get(ctx.guild.roles, name="Admin")
        await voiceChannel.set_permissions(adminRole, view_channel=True, connect=True)
        await voiceChannel.set_permissions(ctx.guild.default_role, view_channel=False, connect=False)

        await ctx.send(
            f'{ctx.message.author.mention} I created the voice channel: "{voiceChannelName}" for you under the {category.name} section!')

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def cleanUpPrivateChannels(self, ctx):
        channelsToDelete = getValidChannelsToDelete(ctx.guild.voice_channels)

        if len(channelsToDelete) == 0:
            await ctx.send("There are no valid channels to delete!")
            return

        view = View(timeout=100)
        view.add_item(ConfirmButton(True, channelsToDelete, ctx.message.author))
        view.add_item(ConfirmButton(False, channelsToDelete, ctx.message.author))
        await ctx.send(
            f'You are about to delete {len(channelsToDelete)} private channel(s). Please Confirm that you want to do this!',
            view=view)
        return

    @tasks.loop(hours=1)
    async def cleanupUnusedPrivateChannels(self):
        guilds = self.client.guilds
        for guild in guilds:
            channelsToDelete = getValidChannelsToDelete(guild.voice_channels)
            await cleanupPrivateVoiceChannels(channelsToDelete, "Skynet Auto Delete Private Voice Channels")


class ConfirmButton(Button):

    def __init__(self, confirm, channelsToDelete, author):
        if confirm:
            super().__init__(label=f'Confirm', style=discord.ButtonStyle.green)
        else:
            super().__init__(label=f'Nevermind', style=discord.ButtonStyle.red)
        self.channelsToDelete = channelsToDelete
        self.author = author
        self.confirm = confirm

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.defer()
            return

        if not self.confirm:
            await interaction.response.edit_message(content=f'Okay I wont do anything!', embed=None, view=None)
            return

        await cleanupPrivateVoiceChannels(self.channelsToDelete, "Manual Deletion")

        await interaction.response.edit_message(
            content=f'Deleted {len(self.channelsToDelete)} channels',
            embed=None,
            view=None)


async def cleanupPrivateVoiceChannels(channelsToDelete, reason):
    for voiceChannel in channelsToDelete:
        await voiceChannel.delete(reason=reason)
    return


def getValidChannelsToDelete(guildVoiceChannels):
    return list(filter(
        lambda voiceChannel: namingConvention in voiceChannel.name and len(voiceChannel.voice_states.keys()) == 0,
        guildVoiceChannels))


async def setup(client):
    await client.add_cog(PrivateChannel(client))
