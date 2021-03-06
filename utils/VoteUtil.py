import time
import asyncio
from discord.utils import get
import datetime

timeforvote = 90 # in seconds

async def hasVotePassed(ctx, channel, messageid, votesrequiredToPass, minVotesRequired = 300):
    message = await channel.fetch_message(messageid)

    upVoteCount = 0
    downVoteCount = 0

    upvotes = get(message.reactions, emoji='👍')
    async for user in upvotes.users():
        upVoteCount += await calculateUserVotingPower(user)

    downvotes = get(message.reactions, emoji='👎')
    async for user in downvotes.users():
        downVoteCount += await calculateUserVotingPower(user)

    # Edit the message because it seems like people cant read and vote on stuff after the vote is completed
    currentMessageContent = message.content
    await message.edit(content=f"**Vote Has Now Ended**\n ~~{currentMessageContent}~~")

    if (upVoteCount + downVoteCount) < minVotesRequired:
        await ctx.send(f"Vote has failed, not enough voting power was used.\nVoting Power Used: {upVoteCount + downVoteCount} Minimum Voting Power Required: {minVotesRequired}")
        return False
    if (upVoteCount - downVoteCount) > votesrequiredToPass:
        await ctx.send("Vote has passed")
        await ctx.send(f"Upvotes: {upVoteCount}, Down Vote Count: {downVoteCount}")
        return True
    else:
        await ctx.send(f"Vote has failed, the proposition has not recieved enough support from the people")
        await ctx.send(f"Upvotes: {upVoteCount}, Down Vote Count: {downVoteCount}, Difference Required: {votesrequiredToPass}")
        return False


# Every 31 days they get 1 vote
async def calculateUserVotingPower(user):
    try:
        return int(((datetime.datetime.now() - user.joined_at).days)/31)
    except:
        return 0

async def setupVote(ctx, voteMessage, timeForVote):
    message = await ctx.send(voteMessage)
    await message.add_reaction('👍')
    await message.add_reaction('👎')
    await asyncio.sleep(timeForVote)
    return message
