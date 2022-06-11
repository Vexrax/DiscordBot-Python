from datetime import datetime

import discord
import pytz
import requests
from discord.ext import commands

leagueImages = {
    "LCS": "https://am-a.akamaihd.net/image/?resize=60:&f=https%3A%2F%2Flolstatic-a.akamaihd.net%2Fesports-assets%2Fproduction%2Fleague%2Flcs-79qe3e0y.png",
    "LEC": "https://am-a.akamaihd.net/image/?resize=60:&f=https%3A%2F%2Flolstatic-a.akamaihd.net%2Fesports-assets%2Fproduction%2Fleague%2Feu-lcs-dgpu3cuv.png",
    "LCK": "https://am-a.akamaihd.net/image/?resize=60:&f=https%3A%2F%2Flolstatic-a.akamaihd.net%2Fesports-assets%2Fproduction%2Fleague%2Flck-7epeu9ot.png",
    "LPL": "https://am-a.akamaihd.net/image/?resize=60:&f=https%3A%2F%2Flolstatic-a.akamaihd.net%2Fesports-assets%2Fproduction%2Fleague%2Flpl-china-6ygsd4c8.png"
}

leagueEsportsAPIBase = "https://esports-api.lolesports.com/persisted/gw/getSchedule"


class Esports(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("Esports Command Ready")

    @commands.command()
    async def schedule(self, ctx, game=None, league=None):
        if game == "league" or game == "leagueoflegends":
            await self.getLeagueOfLegendsSchedule(ctx, league)
        elif game == "dota":
            await self.getAllGamesSchedule(ctx)
        elif game == "CSGO":
            await self.getCSGOSchedule(ctx)
        else:
            await self.getAllGamesSchedule(ctx)

    async def getLeagueOfLegendsSchedule(self, ctx, league):
        embedDict = {}
        resp = requests.get(
            f'{leagueEsportsAPIBase}?hl=en-US&leagueId=98767991299243165%2C98767991302996019%2C98767991310872058%2C98767991314006698',
            headers={'x-api-key': '0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z'})

        if resp.status_code != 200:
            await ctx.send('Something went wrong trying to request the lolesports API')
            return
        data = resp.json()["data"]["schedule"]["events"]

        for match in data:
            if not match["league"]["name"] in embedDict.keys():
                embedDict[match["league"]["name"]] = discord.Embed(title=match["league"]["name"],
                                                                   description=f"Schedule for {match['league']['name']}",
                                                                   color=discord.Color.dark_purple())
                embedDict[match["league"]["name"]].set_thumbnail(url=leagueImages[match['league']['name']])
            if not match["state"] == "completed":
                embedDict[match["league"]["name"]].add_field(name=match["blockName"],
                                                             value=f"{match['match']['teams'][0]['name']} VS {match['match']['teams'][1]['name']}")
                embedDict[match["league"]["name"]].add_field(name="\u200B", value="\u200B")
                embedDict[match["league"]["name"]].add_field(name="\u200B",
                                                             value=f"{self.formatTime(match['startTime'])}")

        if league and league in embedDict.keys():
            await ctx.send(embed=embedDict[league])
            return
        elif not league:
            for key in embedDict.keys():
                embedmessage = embedDict[key]
                await ctx.send(embed=embedmessage)
            return
        await ctx.send("Could not find that league sorry, I only support MAJOR regions right now")

    async def getDotaSchedule(self, ctx):
        await ctx.send("This game schedule command isnt quite ready yet, come back later")

    async def getCSGOSchedule(self, ctx):
        await ctx.send("This game schedule command isnt quite ready yet, come back later")

    async def getAllGamesSchedule(self, ctx):
        await self.getLeagueOfLegendsSchedule(ctx, None)

    def formatTime(self, timestamp):
        est = pytz.timezone('US/Eastern')
        fmt = '%Y-%m-%dT%H:%M:%SZ'
        time = datetime.strptime(timestamp, fmt)
        return time.astimezone(est).strftime('%Y-%m-%d %z %Z')


async def setup(client):
    await client.add_cog(Esports(client))
