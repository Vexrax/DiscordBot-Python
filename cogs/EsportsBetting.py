import os
from enum import Enum

import discord
from discord.ext import commands
from pymongo import MongoClient


class EsportsBetting(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.mongoClient = MongoClient(
            f"mongodb+srv://Dueces:{os.getenv('MONGOPASSWORD')}@cluster0-mzmgc.mongodb.net/test?retryWrites=true&w=majority")
        self.currentEmbed = None
        self.currentBetAmounts = {}
        self.desc = None
        self.team1 = None
        self.team2 = None
        self.matchBettingStatus = BettingStatus.NONE

    @commands.Cog.listener()
    async def on_ready(self):
        print("Randomness Command Ready")

    @commands.command()
    async def StartMatchBet(self, ctx, team1, team2, description):

        self.team1 = team1
        self.team2 = team2
        self.matchBettingStatus = BettingStatus.FINISHED
        self.desc = description
        await self.sendCurrentPointsEmbed(ctx)

    @commands.command()
    async def EndMatchBetting(self, ctx):
        self.matchBettingStatus = BettingStatus.MATCH_ENDED
        await ctx.send("Match Betting is Now Closed!")
        await self.sendCurrentPointsEmbed(ctx)

    async def DeclareWinner(self, ctx, team):
        self.matchBettingStatus = BettingStatus.NONE
        # TODO reward points and update accounts

    @commands.command()
    async def Bet(self, ctx, teamName, amount):
        if self.matchBettingStatus != BettingStatus.ACTIVE:
            await ctx.send("No Live Bets Active!")
            return

        if self.team1.upper() == teamName.upper() or self.team2.upper() == teamName.upper():
            self.currentBetAmounts[ctx.author.name + ctx.author.discriminator] = {"amount": int(amount),
                                                                                  "teamName": teamName}
        await self.sendCurrentPointsEmbed(ctx)

    async def sendCurrentPointsEmbed(self, ctx):
        embed = discord.Embed(title=f'Who Will Win? {self.team1} VS {self.team2}', description=self.description,
                              color=discord.Color.dark_teal())
        embed.set_thumbnail(
            url="https://am-a.akamaihd.net/image/?resize=60:&f=https%3A%2F%2Flolstatic-a.akamaihd.net%2Fesports-assets%2Fproduction%2Fleague%2Flcs-79qe3e0y.png")

        embed.add_field(name=f'{self.team1}', value=f"{self.getAmountBetOn(self.team1)} :money_with_wings:")
        embed.add_field(name=f'{self.team2}', value=f"{self.getAmountBetOn(self.team2)} :money_with_wings:")
        embed.add_field(name="\u200B", value="\u200B", inline=True)

        if len(self.currentBetAmounts.keys()) > 0:
            embed.add_field(name="Betters:", value="\u200B", inline=True)
            embed.add_field(name="\u200B", value="\u200B", inline=True)
            embed.add_field(name="\u200B", value="\u200B", inline=True)

            for key in self.currentBetAmounts:
                embed.add_field(name=key,
                                value=f"{self.currentBetAmounts[key]['amount']} :money_with_wings: On: {self.currentBetAmounts[key]['teamName']}")

        self.currentEmbed = embed
        await ctx.send(embed=embed)

    def getAmountBetOn(self, name):
        total = 0
        for key in self.currentBetAmounts:
            if self.currentBetAmounts[key]["teamName"].upper() == name:
                total += self.currentBetAmounts[key]["amount"]
        return total

    def addBoostedBucks(self, ctx, amount):
        # TODO impl
        return

    def removeBoostedBucks(self, ctx, amount):
        hasAmount = False
        if hasAmount:
            # TODO impl
            return


class BettingStatus(Enum):
    ACTIVE = 1
    FINISHED = 2
    NONE = 3


async def setup(client):
    await client.add_cog(EsportsBetting(client))
