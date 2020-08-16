from discord.utils import get


def isVexrax(id):
    return id == 188313190214533120


async def hasVotePassed(ctx, channel, messageid, votesrequired):
    message = await channel.fetch_message(messageid)

    if ( get(message.reactions, emoji='👍').count + get(message.reactions, emoji='👎').count ) < votesrequired + 2: #2 is for the offset by the default votes by the bot
        await ctx.send("Vote has failed, not enough votes were cast")
        return False
    elif ( get(message.reactions, emoji='👍').count - get(message.reactions, emoji='👎').count ) > 4:
        await ctx.send("Vote has passed, adding the quote to the database")
        return True
    else:
        await ctx.send("Vote has failed, the quote did not receive enough support to be added to the database")
        return False