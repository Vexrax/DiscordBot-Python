import discord
import random
import utils.Util as botUtil
from discord.ext import commands
from pymongo import MongoClient
import os
import time
import utils.VoteUtil as voteUtil

votesRequiredToPass = 150

class CopyPasta(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.mongoClient = MongoClient(f"mongodb+srv://Dueces:{os.getenv('MONGOPASSWORD')}@cluster0-mzmgc.mongodb.net/test?retryWrites=true&w=majority")

    @commands.Cog.listener()
    async def on_ready(self):
        print("CopyPasta Command Ready")

    @commands.command()
    async def copypasta(self, ctx):
        db = self.mongoClient["Skynet"]
        collection = db["CopyPasta"].find({})
        for document in collection:
            descriptionArr = document.get('description').split("\\r\\n") # handling newlines manually because mongo doesnt seem to do it right?
            description = ""
            for line in descriptionArr:
                description += line + "\n\n"
            await ctx.send(embed=discord.Embed( title=document.get("title"), description=description, color=discord.Color.dark_purple()))

    @commands.command()
    async def copypastaadd(self, ctx, pasta, title):

        if botUtil.isVexrax(ctx.message.author.id):
            await self.addCopyPastaToDatabase(ctx, pasta, title)
            await ctx.send("Admin added copypasta, adding to the database")
            return

        voteMessage = f"Vote has been started to add the copypasta '{pasta}' to the list react with 👍 or 👎 to vote on if this quote should be added"
        message = await voteUtil.setupVote(ctx, voteMessage, voteUtil.timeforvote)

        if await voteUtil.hasVotePassed(ctx, ctx.channel, message.id, votesRequiredToPass):
            await self.addCopyPastaToDatabase(ctx, pasta, title)

    async def addCopyPastaToDatabase(self, ctx, pasta, title):
        try:
            db = self.mongoClient["Skynet"]
            collection = db["CopyPasta"]
            collection.insert_one({'title' : title, "description": pasta })
            await ctx.send("Added pasta to database")
        except Exception:
            await ctx.send("Failed to add the quote to the database")

def setup(client):
    client.add_cog(CopyPasta(client))