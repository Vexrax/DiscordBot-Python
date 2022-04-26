import asyncio

import discord
import os
from discord.ext import commands
import utils.Util as botUtil
from cogs.Mute import handleOnMessage

intents = discord.Intents.all()
client = commands.Bot(command_prefix="//", intents=intents)

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
    await client.load_extension(f'cogs.{extension}')

@client.command()
@is_me()
async def reload(ctx, extension):
    await client.unload_extension(f'cogs.{extension}')
    await client.reload_extension(f'cogs.{extension}')

@client.command()
@is_me()
async def unload(ctx, extension):
    await client.unload_extension(f'cogs.{extension}')

@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send('Command not found')
    channel = discord.utils.get(ctx.guild.channels, name="skynet-logs")
    await channel.send(error)

@client.event
async def on_message(message):
    await client.process_commands(message)

    # Custom Message Handling
    await handleOnMessage(message)

async def registerCogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await client.load_extension(f'cogs.{filename[:-3]}')

async def main():
    async with client:
        await registerCogs()
        await client.start(os.getenv('DISCORD'))

asyncio.run(main())

