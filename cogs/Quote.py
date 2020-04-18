import discord
from discord.ext import commands
import youtube_dl
import os
import random
from pymongo import MongoClient

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
    async def quoteadd(self, ctx):
        await ctx.send("quote Add not done yet sorry")

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
        await ctx.send(f'{quote} -{author} {context} {year}')


def setup(client):
    client.add_cog(Quote(client))