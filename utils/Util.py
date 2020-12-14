import time
import asyncio
from discord.utils import get

votesrequired = 8
timeforvote = 90 # in seconds
vexraxId = 188313190214533120
skynetId = 361282484400553985

def getTimeForVote():
    return timeforvote

def getVotesRequired():
    return votesrequired

def isVexrax(id):
    return id == vexraxId

def isSkynet(id):
    return id == skynetId

async def hasVotePassed(ctx, channel, messageid, votesrequired):
    message = await channel.fetch_message(messageid)
    if (get(message.reactions, emoji='👍').count + get(message.reactions, emoji='👎').count ) < votesrequired + 2: #2 is for the offset by the default votes by the bot
        await ctx.send("Vote has failed, not enough votes were cast")
        return False
    elif ( get(message.reactions, emoji='👍').count - get(message.reactions, emoji='👎').count ) > 4:
        await ctx.send("Vote has passed")
        return True
    else:
        await ctx.send("Vote has failed, the proposition has not recieved enough support from the people")
        return False

async def setupVote(ctx, voteMessage):
    message = await ctx.send(voteMessage)
    await message.add_reaction('👍')
    await message.add_reaction('👎')
    await asyncio.sleep(timeforvote)
    return message

async def sendDemocracy(ctx):
        await ctx.send("https://i.imgur.com/z9gqMMw.gif")