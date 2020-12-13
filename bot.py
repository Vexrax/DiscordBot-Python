import discord
import os
from discord.ext import commands
import utils.Util as botUtil

client = commands.Bot(command_prefix="//")

def is_me():
    def predicate(ctx):
        return botUtil.isVexrax(ctx.message.author.id)
    return commands.check(predicate)

@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game('Taking over the world'))
    print('Skynet is online')

@client.event
async def on_member_join(member):
    print(member)

@client.command()
async def ping(ctx):
    await ctx.send('Pong')

@client.command()
@is_me()
async def load(ctx, extension):
    client.load_extension(f'cogs.{extension}')

@client.command()
@is_me()
async def reload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')
    client.reload_extension(f'cogs.{extension}')

@client.command()
@is_me()
async def unload(ctx, extension):
    client.unload_extension(f'cogs.{extension}')

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Command not found')
    user = client.get_user(botUtil.vexraxId)
    await user.send(error)

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')



client.run(os.getenv('DISCORD'))