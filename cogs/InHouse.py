import os

from discord.ext import commands
from pymongo import MongoClient
import requests
import discord
import utils.Util as botUtil
import utils.CacheControl
import operator

from collections import Counter

import json

riotAPIBase = "https://na1.api.riotgames.com"
APIKEY = '' #DEV API key expires daily
ddragonBaseIcon = "http://ddragon.leagueoflegends.com/cdn/10.25.1/img/profileicon/"
minRequiredGames = 5

class InHouse(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.mongoClient = MongoClient(f"mongodb+srv://Dueces:{os.getenv('MONGOPASSWORD')}@cluster0-mzmgc.mongodb.net/test?retryWrites=true&w=majority")
        self.cacheControl = utils.CacheControl.CacheControl()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Inhouse Command Ready")

    @commands.command()
    async def inHouseHelp(self, ctx):
        embed = discord.Embed(title="In House Commands", description="Commands for the inhouse bot", color=discord.Color.dark_teal())
        embed.add_field(name=f"//leaderboard", value=f"Options: (Required)\nwin\nloss\ndpm\ndpg\nhighestUniqueChampions\nlowestUniqueChampions\n")
        embed.add_field(name=f"\u200B", value=f"Options:\ncspm\nkills\ndeaths\nassists")
        embed.add_field(name=f"\u200B", value=f"Options:\navgkills\navgdeaths\navgassists\nhighestavgvisionscore\nlowestavgvisionscore")


        embed.add_field(name=f"//stats", value=f"Options:\nSummoner Name (Case sensitive)")
        embed.add_field(name=f"\u200B", value=f"\u200B")
        embed.add_field(name=f"\u200B", value=f"\u200B")
        await ctx.send(embed=embed)


    @commands.command(aliases=["leaderboards", "lb", "leaderboard", "stats"])
    async def calculateInHouseStats(self, ctx, option):

        # if not botUtil.isVexrax(ctx.message.author.id):
        #     await ctx.send("Maintenance mode enabled, command blocked")
        #     return

        db = self.mongoClient["Skynet"]
        collection = db["InHouses"]

        if option.lower() == 'win':
            embed = await self.calculateGeneralWinStats(collection, True)
        elif option.lower() == 'loss':
            embed = await self.calculateGeneralWinStats(collection, False)
        elif option.lower() == 'dpm':
            embed = await self.calculateGeneralDPMStats(collection)
        elif option.lower() == 'dpg':
            embed = await self.calculateGeneralDPGStats(collection)
        elif option.lower() == 'cspm':
            embed = await self.calculateGeneralCSPMStats(collection)
        elif option.lower() == 'kills':
            embed = await self.calculateGeneralKDAStats(collection, 'kills')
        elif option.lower() == 'deaths':
            embed = await self.calculateGeneralKDAStats(collection, 'deaths')
        elif option.lower() == 'assists':
            embed = await self.calculateGeneralKDAStats(collection, 'assists')
        elif option.lower() == 'avgkills':
            embed = await self.calculateGeneralAverageKDAStats(collection, 'kills')
        elif option.lower() == 'avgdeaths':
            embed = await self.calculateGeneralAverageKDAStats(collection, 'deaths')
        elif option.lower() == 'avgassists':
            embed = await self.calculateGeneralAverageKDAStats(collection, 'assists')
        elif option.lower() == 'highestavgvisionscore':
            embed = await self.calculateGeneralVisionScoreStats(collection, True)
        elif option.lower() == 'lowestavgvisionscore':
            embed = await self.calculateGeneralVisionScoreStats(collection, False)
        elif option.lower() == 'highestuniquechampions':
            embed = await self.calculateUniqueChampionStats(collection, True)
        elif option.lower() == 'lowestuniquechampions':
            embed = await self.calculateUniqueChampionStats(collection, False)
        else:
            embed = await self.generatePlayerStats(option, collection)

        await ctx.send(embed=embed)
        return

    @commands.command()
    async def addMatchForInHouseStats(self, ctx, username):

        if not botUtil.isVexrax(ctx.message.author.id):
            await ctx.send("Due to rate limits/API keys please get vexrax to run this command")
            return
        try:
            encryptedId = await self.getEncryptedSummonerId(username)
            summonerObj = requests.get(f'{riotAPIBase}/lol/spectator/v4/active-games/by-summoner/{encryptedId}?api_key={APIKEY}').json()
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

    async def getEncryptedSummonerId(self, summonerName):
        summonerObj = requests.get(f'{riotAPIBase}/lol/summoner/v4/summoners/by-name/{summonerName}?api_key={APIKEY}').json()
        return summonerObj["id"]

    async def getSummonerIcon(self, summonerName):
        summonerObj = requests.get(f'{riotAPIBase}/lol/summoner/v4/summoners/by-name/{summonerName}?api_key={APIKEY}').json()
        return summonerObj["profileIconId"]

    async def generatePlayerStats(self, summonerName, mongoMatchCollection):

        gameIds = {}
        for document in mongoMatchCollection.find():
            for key in document['gameData']:
                if document['gameData'][key] == summonerName:
                    gameIds[document['matchId']] = key

        if len(gameIds.keys()) == 0:
            return discord.Embed(title=f"Summoner Not Found", description=f"FYI: Names are case sensitive", color=discord.Color.dark_red())

        playerStats = Counter({})

        goldDiffs = Counter({})
        xpDiffs = Counter({})
        csDiffs = Counter({})

        gameCount = 0
        totalGameTime = 0
        for matchId in gameIds:
            matchData = await self.cacheControl.getMatchReport(matchId)
            statsForMatch = Counter(self.findStatsFromParticipantList(matchData['participants'], gameIds[matchId]))
            diffsForMatch = self.generatePlayerDiffsFromMatch(matchData['participants'], gameIds[matchId])

            goldDiffs.update(diffsForMatch["goldPerMinDeltas"])
            xpDiffs.update(diffsForMatch["xpPerMinDeltas"])
            csDiffs.update(diffsForMatch["creepsPerMinDeltas"])
            playerStats = statsForMatch + playerStats

            gameCount += 1
            totalGameTime += int(matchData['gameDuration'] / 60)

        return await self.generateEmbedForPlayerStats(gameCount, playerStats, summonerName, totalGameTime, csDiffs, goldDiffs, xpDiffs, Counter(gameIds.values()), f"{ddragonBaseIcon}{await self.getSummonerIcon(summonerName)}.png")

    async def generateEmbedForPlayerStats(self, gameCount, playerStats, summonerName, totalGameTime, csDiffs, goldDiffs, xpDiffs, champions, iconLink):
        embed = discord.Embed(title=f"{summonerName}'s InHouse Stats", description=f"Cool Stats", color=discord.Color.dark_blue())
        embed.set_thumbnail(url=iconLink)
        embed.set_author(name=summonerName, icon_url=iconLink)
        embed.add_field(name="Games Played", value=f"{gameCount}")
        embed.add_field(name="Win Rate", value=f"{round(playerStats['win'] / gameCount, 2) * 100}")
        embed.add_field(name="Unique Champions", value=f"{len(champions.keys())}")

        embed.add_field(name="Damage Per Gold", value=f"{round(playerStats['totalDamageDealtToChampions'] / playerStats['goldEarned'], 2)}", inline=True)
        embed.add_field(name="Damage Per Minute", value=f"{round(playerStats['totalDamageDealtToChampions'] / totalGameTime, 2)}", inline=True )
        embed.add_field(name="\u200B", value="\u200B")

        embed.add_field(name="Average Kills Per Game", value=f"{round(playerStats['kills'] / gameCount, 2)}", inline=True)
        embed.add_field(name="Average Deaths Per Game", value=f"{round(playerStats['deaths'] / gameCount, 2)}", inline=True)
        embed.add_field(name="Average Assists Per Game", value=f"{round(playerStats['assists'] / gameCount, 2)}", inline=True)

        embed.add_field(name="Objective Damage Per Game", value=f"{round(playerStats['damageDealtToObjectives'] / gameCount, 2)}", inline=True)
        embed.add_field(name="Turrets Killed", value=f"{playerStats['turretKills']}" , inline=True)
        embed.add_field(name="\u200B", value="\u200B")

        embed.add_field(name="CS per min", value=f"{round((playerStats['totalMinionsKilled'] + playerStats['neutralMinionsKilled']) / totalGameTime, 2)}", inline=True)
        embed.add_field(name="Average Vision Score", value=f"{round((playerStats['visionScore']) / gameCount, 2)}", inline=True)
        embed.add_field(name="\u200B", value="\u200B")

        embed.add_field(name="Differentials", value="This Section is experimental, stats may be completely wrong", inline=True)
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="\u200B", value="\u200B")

        embed.add_field(name="XP Diff at 10 (experimental)", value=f"{round((xpDiffs['0-10'] * 10 )/ gameCount, 2)}", inline=True)
        embed.add_field(name="Gold Diff at 10 (experimental)", value=f"{round((goldDiffs['0-10'] * 10) / gameCount, 2)}", inline=True)
        embed.add_field(name="CS Diff at 10 (experimental)", value=f"{round((csDiffs['0-10'] * 10) / gameCount, 2)}", inline=True)


        embed.add_field(name="XP Diff at 20 (experimental)", value=f"{round(((xpDiffs['0-10'] * 10 ) + (xpDiffs['10-20'] * 10 )) / gameCount, 2)}", inline=True)
        embed.add_field(name="Gold Diff at 20 (experimental)", value=f"{round(((goldDiffs['0-10'] * 10) + (goldDiffs['10-20'] * 10)) / gameCount, 2)}", inline=True)
        embed.add_field(name="CS Diff at 20 (experimental)", value=f"{round(((csDiffs['0-10'] * 10) + (csDiffs['10-20'] * 10)) / gameCount, 2)}", inline=True)

        return embed

    def findStatsFromParticipantList(self, participantList, targetChampion):
        for champStats in participantList:
            if(str(champStats['championId']) == targetChampion):
                return champStats['stats']
        return {}

    def generatePlayerDiffsFromMatch(self, participantList, targetChampion):
        timelineTarget = {}
        particpantId = 0
        lanePartnerParticipantId = 0
        for champStats in participantList:
            if(str(champStats['championId']) == targetChampion):
                timelineTarget = champStats['timeline']
                particpantId = champStats['participantId']

        if particpantId <= 5:
            lanePartnerParticipantId = particpantId + 5
        else:
            lanePartnerParticipantId = particpantId - 5

        for champStats in participantList:
            if(champStats['participantId'] == lanePartnerParticipantId):

                xp = Counter(timelineTarget["xpPerMinDeltas"])
                cs = Counter(timelineTarget["creepsPerMinDeltas"])
                gold = Counter(timelineTarget["goldPerMinDeltas"])

                xp.subtract(Counter(champStats['timeline']["xpPerMinDeltas"]))
                cs.subtract(Counter(champStats['timeline']["creepsPerMinDeltas"]))
                gold.subtract(Counter(champStats['timeline']["goldPerMinDeltas"]))

                return {
                    "creepsPerMinDeltas": cs,
                    "xpPerMinDeltas": xp,
                    "goldPerMinDeltas": gold
                }


    async def calculateGeneralWinStats(self, collection, highest):
        sortedDict = await self.generateLeaderboardDict(collection, 'averagePercent', highest, 'win', 'totalGames')
        lbName = "Top 5"
        if not highest:
            lbName = "Bottom 5"
        return self.generateLeaderboardEmbed(sortedDict, f"{lbName} Winrate players", f"Out of {len(sortedDict)} players, these players have the {lbName} winrate")

    async def calculateGeneralDPMStats(self, collection):
        sortedDict = await self.generateLeaderboardDict(collection, 'averageGameTime', True, 'totalDamageDealtToChampions', 'totalGameTime')
        return self.generateLeaderboardEmbed(sortedDict, "Top 5 DPM players", "DPM is a statistic that calculates your average damage per minute")

    async def calculateGeneralDPGStats(self, collection):
        sortedDict = await self.generateLeaderboardDict(collection, 'average', True, 'totalDamageDealtToChampions', 'goldEarned')
        return self.generateLeaderboardEmbed(sortedDict, "Top 5 DPG players", "DPG is a statistic that shows how well a given player uses the gold they are given")

    async def calculateGeneralCSPMStats(self, collection):
        sortedDict = await self.generateLeaderboardDict(collection, 'multiaddaverageGameTime', True, 'totalMinionsKilled', 'neutralMinionsKilled', 'totalGameTime')
        return self.generateLeaderboardEmbed(sortedDict, "Top 5 CS/M players", "Just CS per Min")

    async def calculateGeneralKDAStats(self, collection, type):
        sortedDict = await self.generateLeaderboardDict(collection, 'single', True, type)
        return self.generateLeaderboardEmbed(sortedDict, f"Top 5 {type} players", f"Highest total {type} count in the league")

    async def calculateGeneralVisionScoreStats(self, collection, highest):
        sortedDict = await self.generateLeaderboardDict(collection, 'average', highest, 'visionScore', 'totalGames')
        lbName = "Top"
        if not highest:
            lbName = "Bottom"
        return self.generateLeaderboardEmbed(sortedDict, f"{lbName} 5 Average Vision Score players", f"Cool Stats")

    async def calculateGeneralAverageKDAStats(self, collection, type):
        sortedDict = await self.generateLeaderboardDict(collection, 'average', True, type, 'totalGames')
        return self.generateLeaderboardEmbed(sortedDict, f"Top 5 Average {type} players", f"Highest average {type} count in the league")

    async def calculateUniqueChampionStats(self, collection, highest):
        playerChampionDict = {}
        for document in collection.find():
            for championId in document['gameData'].keys():
                if document['gameData'][championId] not in playerChampionDict:
                    playerChampionDict[document['gameData'][championId]] = set()
                playerChampionDict[document['gameData'][championId]].add(int(championId))

        uniques = {}
        for key in playerChampionDict:
            uniques[key] = len(playerChampionDict[key])
        sortedDict = sorted(uniques.items(), key=operator.itemgetter(1), reverse=highest)
        lbName = "Top"
        if not highest:
            lbName = "Bottom"
        return self.generateLeaderboardEmbed(sortedDict, f"{lbName} 5 players by unique champions ", f"Unique champions played in inhouse Matches")

    async def generateLeaderboardDict(self, collection, type, sortDecending, *argv):
        playersData = await self.aggregateStatsForEveryone(collection)
        AVGKDADict = {}
        for key in playersData:
            if playersData[key]['totalGames'] >= minRequiredGames:
                if type == "average":
                    AVGKDADict[key] = round(playersData[key][argv[0]] / playersData[key][argv[1]], 2)
                elif type == "averageGameTime":
                    AVGKDADict[key] = round(playersData[key][argv[0]] / (playersData[key][argv[1]] / 60), 2)
                elif type == "averagePercent":
                    AVGKDADict[key] = round(playersData[key][argv[0]] / playersData[key][argv[1]], 2) * 100
                elif type == "single":
                    AVGKDADict[key] = round(playersData[key][argv[0]], 2)
                elif type == "multiaddaverageGameTime":
                    AVGKDADict[key] = round((playersData[key][argv[0]] + playersData[key][argv[1]]) / (playersData[key][argv[2]] / 60), 2)

        return sorted(AVGKDADict.items(), key=operator.itemgetter(1), reverse=sortDecending)

    def generateLeaderboardEmbed(self, sortedDict, title, subtitle):
        embed = discord.Embed(title=title, description=subtitle, color=discord.Color.dark_blue())
        i = 0
        emojiMap = {
            0 : ":first_place:",
            1: ":second_place:",
            2: ":third_place:",
        }
        for key in sortedDict:
            emoji = ""
            if(i < 3):
                emoji = emojiMap[i]
            embed.add_field(name=f"{emoji} {key[0]}", value=f"\u200B")
            embed.add_field(name="\u200B", value="\u200B")
            embed.add_field(name=f"{key[1]}", value="\u200B")
            i += 1
            if i == 5:
                return embed
        return embed

    async def aggregateStatsForEveryone(self, collection):
        playersData = {}
        for document in collection.find():
            matchData = await self.cacheControl.getMatchReport(document["matchId"])
            for player in matchData['participants']:
                name = document['gameData'][str(player["championId"])]
                stats = Counter(player["stats"])
                if name not in playersData:
                    playersData[name] = Counter({})
                    playersData[name]['totalGameTime'] = 0
                    playersData[name]['totalGames'] = 0
                playersData[name] = playersData[name] + stats
                playersData[name]['totalGameTime'] += matchData["gameDuration"]
                playersData[name]['totalGames'] += 1


        return playersData
def setup(client):
    client.add_cog(InHouse(client))