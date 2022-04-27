import datetime
import os

import discord
from discord.ext import commands
from discord.ui import Button, View
from pymongo import MongoClient
from discord.ext import tasks
from utils.EmbedBuilder import generateReminderEmbed


class RemindMe(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.mongoClient = MongoClient(
            f"mongodb+srv://Dueces:{os.getenv('MONGOPASSWORD')}@cluster0-mzmgc.mongodb.net/test?retryWrites=true&w=majority")
        self.units = {
            "minutes" : lambda minutes: datetime.datetime.now() + datetime.timedelta(minutes=minutes),
            "hours": lambda hours: datetime.datetime.now() + datetime.timedelta(hours=hours),
            "days": lambda days: datetime.datetime.now() + datetime.timedelta(days=days),
            "months": lambda months: datetime.datetime.now() + datetime.timedelta(days=months*30) # Using an approximation here
        }

    @commands.Cog.listener()
    async def on_ready(self):
        print("Remindme Command Ready")
        self.checkReminders.start()

    @commands.command()
    async def remindMe(self, ctx, message, time):
        view = View(timeout=100)
        for key in self.units:
            view.add_item(ReminderButton(ctx.author, ctx.channel.guild.id, ctx.channel.name, message, time, key, discord.ButtonStyle.blurple, self.units.get(key)))
        await ctx.send(embed=generateReminderEmbed(message), view=view)
        return

    @tasks.loop(minutes=1.5)
    async def checkReminders(self):
        db = self.mongoClient["Skynet"]
        collection = db["Reminders"]
        for document in collection.find():
            if datetime.datetime.timestamp(datetime.datetime.now()) * 1000 < document.get("timestamp"):
                continue

            collection.delete_one(document)
            guild = self.client.get_guild(document.get('guild'))
            channel = discord.utils.get(guild.channels, name=document.get('channel'))
            await channel.send(f'{guild.get_member(document.get("id")).mention} You asked me to remind you about: "{document.get("reminder")}"')

    @checkReminders.before_loop
    async def before_my_task(self):
        await self.client.wait_until_ready()  # wait until the bot logs in


class ReminderButton(Button):

    def __init__(self, author, guildId, channelName, message, amount, timeunit, style, func):
        super().__init__(label=f'{amount} {timeunit}', style=style)
        self.func = func
        self.message = message
        self.amount = amount
        self.timeunit = timeunit
        self.author = author
        self.guildId = guildId
        self.channelName = channelName

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            await interaction.response.defer()
            return

        try:
            timestamp = self.func(int(self.amount))
            mongoClient = MongoClient(f"mongodb+srv://Dueces:{os.getenv('MONGOPASSWORD')}@cluster0-mzmgc.mongodb.net/test?retryWrites=true&w=majority")
            db = mongoClient["Skynet"]
            collection = db["Reminders"]
            collection.insert_one({'id': self.author.id,
                                   "reminder": self.message,
                                   "guild": self.guildId,
                                   "channel": self.channelName,
                                   "timestamp": datetime.datetime.timestamp(timestamp) * 1000
                                   })
            await interaction.response.edit_message(
                content=f'{self.author.mention} I will remind you in {self.amount} {self.timeunit} for the reminder: "{self.message}"',
                embed=None,
                view=None)
        except ValueError:
            await interaction.response.edit_message(content="Something went wrong. Try again later!", view=None)

async def setup(client):
    await client.add_cog(RemindMe(client))
