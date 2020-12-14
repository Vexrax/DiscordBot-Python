import time
import asyncio
from discord.utils import get

vexraxId = 188313190214533120
skynetId = 361282484400553985

def isVexrax(id):
    return id == vexraxId

def isSkynet(id):
    return id == skynetId

async def sendDemocracy(ctx):
        await ctx.send("https://i.imgur.com/z9gqMMw.gif")