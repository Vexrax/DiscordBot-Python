import os

from discord.ext import commands
from pymongo import MongoClient
import discord
import utils.Util as botUtil
import utils.CacheControl
import operator
import matplotlib.pyplot as plt
import io

import json

from utils.EmbedBuilder import generateLeaderboardEmbed, generateEmbedForPlayerStats

ddragonBase = "http://ddragon.leagueoflegends.com/cdn/10.25.1"
ddragonBaseIcon = f"{ddragonBase}/img/profileicon/"

minRequiredGames = 5
maxDisplayLeaderboard = 5

class InHouse(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.mongoClient = MongoClient(f"mongodb+srv://Dueces:{os.getenv('MONGOPASSWORD')}@cluster0-mzmgc.mongodb.net/test?retryWrites=true&w=majority")
        self.cacheControl = utils.CacheControl.CacheControl()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Inhouse Command Ready")

    @commands.command(aliases=["inhousehelp"])
    async def inHouseHelp(self, ctx):
        embed = discord.Embed(title="In House Commands", description="Commands for the inhouse bot", color=discord.Color.dark_teal())
        embed.add_field(name=f"//leaderboard", value=f"Options: (Required)\nwin\nloss\ndpm\ndpg\nhighestUniqueChampions\nlowestUniqueChampions\n")
        embed.add_field(name=f"\u200B", value=f"Options:\ncspm\nkills\ndeaths\nassists")
        embed.add_field(name=f"\u200B", value=f"Options:\navgkills\navgdeaths\navgassists\nhighestavgvisionscore\nlowestavgvisionscore")


        embed.add_field(name=f"//stats", value=f"Options:\nSummoner Name (Case sensitive)")
        embed.add_field(name=f"\u200B", value=f"\u200B")
        embed.add_field(name=f"\u200B", value=f"\u200B")
        await ctx.send(embed=embed)

    @commands.command()
    async def imageTest(self, ctx):
        plt.figure()
        plt.plot([1, 2])
        plt.title("test")
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        await ctx.send(file=discord.File(fp=buf, filename='image.png'))

    @commands.command(aliases=["leaderboards", "lb", "leaderboard", "stats"])
    async def calculateInHouseStats(self, ctx, option):

        # if not botUtil.isVexrax(ctx.message.author.id):
        #     await ctx.send("Maintenance mode enabled, command blocked")
        #     return

        if option.lower() == 'win':
            embed = await self.calculateGeneralWinStats(True)
        elif option.lower() == 'loss':
            embed = await self.calculateGeneralWinStats(False)
        elif option.lower() == 'dpm':
            embed = await self.calculateGeneralDPMStats()
        elif option.lower() == 'dpg':
            embed = await self.calculateGeneralDPGStats()
        elif option.lower() == 'cspm':
            embed = await self.calculateGeneralCSPMStats()
        elif option.lower() == 'kills':
            embed = await self.calculateGeneralKDAStats('kills')
        elif option.lower() == 'deaths':
            embed = await self.calculateGeneralKDAStats('deaths')
        elif option.lower() == 'assists':
            embed = await self.calculateGeneralKDAStats('assists')
        elif option.lower() == 'avgkills':
            embed = await self.calculateGeneralAverageKDAStats('kills')
        elif option.lower() == 'avgdeaths':
            embed = await self.calculateGeneralAverageKDAStats( 'deaths')
        elif option.lower() == 'avgassists':
            embed = await self.calculateGeneralAverageKDAStats('assists')
        elif option.lower() == 'highestavgvisionscore':
            embed = await self.calculateGeneralVisionScoreStats(True)
        elif option.lower() == 'lowestavgvisionscore':
            embed = await self.calculateGeneralVisionScoreStats( False)
        elif option.lower() == 'highestuniquechampions':
            embed = await self.calculateUniqueChampionStats(True)
        elif option.lower() == 'lowestuniquechampions':
            embed = await self.calculateUniqueChampionStats(False)
        elif option.lower() == 'lowestkp':
            embed = await self.calculateAverageKillParticipation(True)
        elif option.lower() == 'highestkp':
            embed = await self.calculateAverageKillParticipation(False)
        elif option.lower() == 'ban':
            embed = await self.calculateBanStats()
        else:
            embed = await self.generatePlayerStats(option)

        await ctx.send(embed=embed)
        return

    @commands.command()
    async def addMatchForInHouseStats(self, ctx, username):

        if not botUtil.isVexrax(ctx.message.author.id) and not ctx.message.author.id == 105128588411437056:
            await ctx.send("Due to rate limits/API keys please get vexrax to run this command")
            return
        try:
            encryptedId = await self.cacheControl.getEncryptedSummonerId(username)
            summonerObj = await self.cacheControl.getLiveMatch(encryptedId)
            participantMap = {}
            for summoner in summonerObj['participants']:
                participantMap[str(summoner['championId'])] = str(summoner['summonerName'])
            db = self.mongoClient["Skynet"]
            collection = db["InHouses"]
            finalDict = {'matchId': summonerObj['gameId'], "gameData": participantMap}
            collection.insert_one(finalDict)
            await ctx.send(f"Added Match {summonerObj['gameId']} to the match database")
        except Exception as e:
            await ctx.send(f"Something went wrong {e} ")
            return

    async def manualAddMatch(self, ctx):
        f = open("C:\\Users\\Joshua\\Documents\\Repos\\DiscordBot-Python\\cogs\\temp.json", "r")
        data = json.load(f)
        participantMap = {}
        temp = {}
        for player in data['participants']:
            participantMap[str(player['championId'])] = str(player['participantId'])

        for player2 in data['participantIdentities']:
            temp[str(player2['participantId'])] = str(player2['player']['summonerName'])

        for key in participantMap:
            participantMap[key] = temp[participantMap[key]]


        try:
            db = self.mongoClient["Skynet"]
            collection = db["InHouses"]
            finalDict = {'matchId': data['gameId'], "gameData": participantMap}
            collection.insert_one(finalDict)
        except Exception as e:
            print(e)

    async def generatePlayerStats(self, summonerName):

        playerStats = await self.cacheControl.getStats(summonerName)
        if len(playerStats.keys()) == 0:
            return discord.Embed(title=f"Summoner Not Found", description=f"FYI: Names are case sensitive", color=discord.Color.dark_red())
        embed = await generateEmbedForPlayerStats(summonerName, playerStats, f"{ddragonBaseIcon}{await self.cacheControl.getSummonerIcon(summonerName)}.png")
        return embed

    async def calculateGeneralWinStats(self, highest):
        sortedDict = await self.generateLeaderboardDict('averagePercent', highest, 'win', 'totalGames')
        lbName = "Top 5"
        if not highest:
            lbName = "Bottom 5"
        return generateLeaderboardEmbed(sortedDict, f"{lbName} Winrate players", f"Out of {len(sortedDict)} players, these players have the {lbName} winrate")

    async def calculateGeneralDPMStats(self):
        sortedDict = await self.generateLeaderboardDict('averageGameTime', True, 'totalDamageDealtToChampions', 'totalGameTime')
        return generateLeaderboardEmbed(sortedDict, "Top 5 DPM players", "DPM is a statistic that calculates your average damage per minute")

    async def calculateGeneralDPGStats(self):
        sortedDict = await self.generateLeaderboardDict('average', True, 'totalDamageDealtToChampions', 'goldEarned')
        return generateLeaderboardEmbed(sortedDict, "Top 5 DPG players", "DPG is a statistic that shows how well a given player uses the gold they are given")

    async def calculateGeneralCSPMStats(self):
        sortedDict = await self.generateLeaderboardDict('multiaddaverageGameTime', True, 'totalMinionsKilled', 'neutralMinionsKilled', 'totalGameTime')
        return generateLeaderboardEmbed(sortedDict, "Top 5 CS/M players", "Just CS per Min")

    async def calculateGeneralKDAStats(self, type):
        sortedDict = await self.generateLeaderboardDict('single', True, type)
        return generateLeaderboardEmbed(sortedDict, f"Top 5 {type} players", f"Highest total {type} count in the league")

    async def calculateAverageKillParticipation(self, highest):
        sortedDict = await self.generateLeaderboardDict('summedAvg', highest, 'kills', 'assists', 'totalKillsAvailable')
        lbName = "Top 5"
        if not highest:
            lbName = "Bottom 5"
        return generateLeaderboardEmbed(sortedDict, f"{lbName} KP players", f"Highest total Kill Participation count in the league")

    async def calculateGeneralVisionScoreStats(self, highest):
        sortedDict = await self.generateLeaderboardDict('average', highest, 'visionScore', 'totalGames')
        lbName = "Top"
        if not highest:
            lbName = "Bottom"
        return generateLeaderboardEmbed(sortedDict, f"{lbName} 5 Average Vision Score players", f"Cool Stats")

    async def calculateGeneralAverageKDAStats(self, type):
        sortedDict = await self.generateLeaderboardDict('average', True, type, 'totalGames')
        return generateLeaderboardEmbed(sortedDict, f"Top 5 Average {type} players", f"Highest average {type} count in the league")

    async def calculateUniqueChampionStats(self, highest):
        uniques = await self.cacheControl.getStats('unique')
        sortedDict = sorted(uniques.items(), key=operator.itemgetter(1), reverse=highest)
        lbName = "Top"
        if not highest:
            lbName = "Bottom"
        return generateLeaderboardEmbed(sortedDict, f"{lbName} 5 players by unique champions ", f"Unique champions played in inhouse Matches")

    async def calculateBanStats(self):
        data = await self.cacheControl.getStats('ban')
        sortedDict = sorted(data.items(), key=operator.itemgetter(1), reverse=True)
        return generateLeaderboardEmbed(sortedDict, "Highest Ban Champions", "These are the most banned champions")

    async def generateLeaderboardDict(self, type, sortDecending, *argv):
        playersData = await self.cacheControl.getStats('general')
        LeaderBoardDict = {}
        for key in playersData:
            if playersData[key]['totalGames'] >= minRequiredGames:
                if type == "average":
                    LeaderBoardDict[key] = round(playersData[key][argv[0]] / playersData[key][argv[1]], 2)
                elif type == "averageGameTime":
                    LeaderBoardDict[key] = round(playersData[key][argv[0]] / (playersData[key][argv[1]] / 60), 2)
                elif type == "averagePercent":
                    LeaderBoardDict[key] = round(playersData[key][argv[0]] / playersData[key][argv[1]], 2) * 100
                elif type == "single":
                    LeaderBoardDict[key] = round(playersData[key][argv[0]], 2)
                elif type == "multiaddaverageGameTime":
                    LeaderBoardDict[key] = round((playersData[key][argv[0]] + playersData[key][argv[1]]) / (playersData[key][argv[2]] / 60), 2)
                elif type == "summedAvg":
                    LeaderBoardDict[key] = round((playersData[key][argv[0]] + playersData[key][argv[1]]) / (playersData[key][argv[2]]), 2)


        return sorted(LeaderBoardDict.items(), key=operator.itemgetter(1), reverse=sortDecending)

    async def generateLeaderboardImage(self, sortedDict, ctx):
        channel = discord.utils.get(ctx.guild.channels, name='skynet-logs')

        nameLabels = []
        values = []
        i = 0

        for tup in sortedDict:
            nameLabels.append(tup[0])
            values.append(tup[1])
            i+=1
            if i == maxDisplayLeaderboard:
                break

        values.reverse()
        nameLabels.reverse()

        plt.rcdefaults()
        fig, ax = plt.subplots()
        ax.barh([0,1,2,3,4], values, align='center')
        ax.set_yticks([0,1,2,3,4])
        ax.set_yticklabels(nameLabels)
        ax.set_xlabel('WINS')
        ax.set_title('THE BEST OF THE BEST')
        ax.set_facecolor("#2C2F33")

        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        x = await channel.send(file=discord.File(fp=buf, filename='image.png'))
        buf.close()
        return x.attachments[0].url


def setup(client):
    client.add_cog(InHouse(client))