import discord
from discord.ext import commands
import os
import random
import time
from pymongo import MongoClient
from discord.utils import get
import utils.Util as botUtil

votesrequired = 5
timeforvote = 90 # in seconds

class Quote(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.mongoClient = MongoClient(f"mongodb+srv://Dueces:{os.getenv('MONGOPASSWORD')}@cluster0-mzmgc.mongodb.net/test?retryWrites=true&w=majority")

    @commands.Cog.listener()
    async def on_ready(self):
        print("Quote Command Ready")

    @commands.command()
    async def quote(self, ctx):
       await self.findRandomQuote(ctx)

    @commands.command()
    async def quoteadd(self, ctx, quote, author, year):

        if botUtil.isVexrax(ctx.message.author.id):
            await self.addQuoteToDatabase(ctx, author, year, quote)
            await ctx.send("Admin added quote, adding to the database")
            return

        message = await ctx.send(f"Vote has been started to add the quote '{quote} -{author} {year} to the list react with 👍 or 👎 to vote on if this quote should be added")
        await message.add_reaction('👍')
        await message.add_reaction('👎')
        time.sleep(timeforvote)
        if await self.votePassed(ctx, ctx.channel, message.id):
            await self.addQuoteToDatabase(ctx, author, year, quote)

    @commands.command()
    async def quote(self, ctx):
       await self.findRandomQuote(ctx)

    @commands.command()
    async def quotefrom(self, ctx, author):
       try:
        await self.findRandomQuote(ctx, {"author": author.capitalize()})
       except Exception:
        print(Exception)
        await ctx.send("Could not find a quote from that person")

    async def findRandomQuote(self, ctx, params = {}):
        db = self.mongoClient["Skynet"]
        collection = db["Quotes"]
        doc = collection.find(params)
        randomInt = random.randint(0, doc.count()-1)
        result = doc.limit(1).skip(randomInt)
        randomDoc = result.next()
        quote, author, context, year = randomDoc.get('quote'), randomDoc.get('author'), randomDoc.get('context'), randomDoc.get('year')
        await ctx.send(f'"{quote}" -{author} {context} {year}')

    async def votePassed(self, ctx, channel, messageid):
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

    async def addQuoteToDatabase(self, ctx, author, year, quote):
        try:
            db = self.mongoClient["Skynet"]
            collection = db["Quotes"]
            collection.insert_one({'quote' : quote, "author": author, "year": year, "context": ""})
            await ctx.send("Added quote to database")
        except Exception:
            await ctx.send("Failed to add the quote to the database")

def setup(client):
    client.add_cog(Quote(client))