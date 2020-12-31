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

class InHouse(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.mongoClient = MongoClient(f"mongodb+srv://Dueces:{os.getenv('MONGOPASSWORD')}@cluster0-mzmgc.mongodb.net/test?retryWrites=true&w=majority")
        self.cacheControl = utils.CacheControl.CacheControl()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Inhouse Command Ready")

    @commands.command()
    async def calculateInHouseStats(self, ctx, option):

        # if not botUtil.isVexrax(ctx.message.author.id):
        #     await ctx.send("Maintenance mode enabled, command blocked")
        #     return

        db = self.mongoClient["Skynet"]
        collection = db["InHouses"]

        if option.lower() == 'win':
            embed = await self.calculateGeneralWinStats(collection)
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
        gameCount = 0
        totalGameTime = 0
        for matchId in gameIds:
            matchData = await self.cacheControl.getMatchReport(matchId)
            statsForMatch = Counter(self.findStatsFromParticipantList(matchData['participants'], gameIds[matchId]))
            playerStats = statsForMatch + playerStats
            gameCount += 1
            totalGameTime += int(matchData['gameDuration'] / 60)

        return await self.generateEmbedForPlayerStats(gameCount, playerStats, summonerName, totalGameTime, f"{ddragonBaseIcon}{await self.getSummonerIcon(summonerName)}.png")

    async def generateEmbedForPlayerStats(self, gameCount, playerStats, summonerName, totalGameTime, iconLink):
        embed = discord.Embed(title=f"{summonerName}'s InHouse Stats", description=f"Cool Stats", color=discord.Color.dark_blue())
        embed.set_thumbnail(url=iconLink)
        embed.add_field(name="Win Rate", value=f"{round(playerStats['win'] / gameCount, 2) * 100}")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="Damage Per Gold", value=f"{round(playerStats['totalDamageDealtToChampions'] / playerStats['goldEarned'], 2)}")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="Damage Per Minute", value=f"{round(playerStats['totalDamageDealtToChampions'] / totalGameTime, 2)}")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="Average Kills Per Game", value=f"{round(playerStats['kills'] / gameCount, 2)}")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="Average Deaths Per Game", value=f"{round(playerStats['deaths'] / gameCount, 2)}")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="Average Assists Per Game", value=f"{round(playerStats['assists'] / gameCount, 2)}")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="CS per min", value=f"{round(playerStats['totalMinionsKilled'] / totalGameTime, 2)}")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="Turrets Killed", value=f"{playerStats['turretKills']}")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="Objective Damage Per Game",
                        value=f"{round(playerStats['damageDealtToObjectives'] / gameCount, 2)}")
        embed.add_field(name="\u200B", value="\u200B")
        embed.add_field(name="\u200B", value="\u200B")
        return embed

    def findStatsFromParticipantList(self, participantList, targetChampion):
        for champStats in participantList:
            if(str(champStats['championId']) == targetChampion):
                return champStats['stats']
        return {}

    async def calculateGeneralWinStats(self, collection):
        playersData = await self.aggregateStatsForEveryone(collection)
        winDict = {}
        for key in playersData:
            winDict[key] = round(playersData[key]['win'] / playersData[key]['totalGames'], 2) * 100
        sortedDict = sorted(winDict.items(), key=operator.itemgetter(1), reverse=True)
        return self.generateLeaderboardEmbed(sortedDict, "Top 5 Winrate players", "Cool Stats")

    async def calculateGeneralDPMStats(self, collection):
        playersData = await self.aggregateStatsForEveryone(collection)
        DPMDict = {}
        for key in playersData:
            DPMDict[key] = round(playersData[key]['totalDamageDealtToChampions'] / (playersData[key]['totalGameTime'] / 60), 2)
        sortedDict = sorted(DPMDict.items(), key=operator.itemgetter(1), reverse=True)
        return self.generateLeaderboardEmbed(sortedDict, "Top 5 DPM players", "Cool Stats")

    async def calculateGeneralDPGStats(self, collection):
        playersData = await self.aggregateStatsForEveryone(collection)
        DPMDict = {}
        for key in playersData:
            DPMDict[key] = round(playersData[key]['totalDamageDealtToChampions'] / playersData[key]['goldEarned'], 2)
        sortedDict = sorted(DPMDict.items(), key=operator.itemgetter(1), reverse=True)
        return self.generateLeaderboardEmbed(sortedDict, "Top 5 DPG players", "Cool Stats")

    async def calculateGeneralCSPMStats(self, collection):
        playersData = await self.aggregateStatsForEveryone(collection)
        DPMDict = {}
        for key in playersData:
            DPMDict[key] = round(playersData[key]['totalMinionsKilled'] / (playersData[key]['totalGameTime'] / 60), 2)
        sortedDict = sorted(DPMDict.items(), key=operator.itemgetter(1), reverse=True)
        return self.generateLeaderboardEmbed(sortedDict, "Top 5 CS/M players", "Cool Stats")

    async def calculateGeneralKDAStats(self, collection, type):
        playersData = await self.aggregateStatsForEveryone(collection)
        DPMDict = {}
        for key in playersData:
            DPMDict[key] = round(playersData[key][type], 2)
        sortedDict = sorted(DPMDict.items(), key=operator.itemgetter(1), reverse=True)
        return self.generateLeaderboardEmbed(sortedDict, f"Top 5 {type} players", "Cool Stats")

    async def calculateGeneralAverageKDAStats(self, collection, type):
        playersData = await self.aggregateStatsForEveryone(collection)
        DPMDict = {}
        for key in playersData:
            DPMDict[key] = round(playersData[key][type] / playersData[key]['totalGames'], 2)
        sortedDict = sorted(DPMDict.items(), key=operator.itemgetter(1), reverse=True)
        return self.generateLeaderboardEmbed(sortedDict, f"Top 5 Average {type} players", "Cool Stats")

    def generateLeaderboardEmbed(self, sortedDict, title, subtitle):
        embed = discord.Embed(title=title, description=subtitle, color=discord.Color.dark_blue())
        i = 0
        for key in sortedDict:
            embed.add_field(name=f"{key[0]}", value=f"\u200B")
            embed.add_field(name="\u200B", value="\u200B")
            embed.add_field(name=f"{key[1]}", value="\u200B")
            i += 1
            if i > 5:
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