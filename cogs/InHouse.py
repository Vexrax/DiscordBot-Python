import json
import operator
import os
from collections import Counter

import discord
from discord.ext import commands
from pymongo import MongoClient

import utils.CacheControl
from utils.EmbedBuilder import generateLeaderboardEmbed, generateEmbedForPlayerStats, generateInHouseHelpEmbed, \
    generateMatchEmbed, generateGeneralStatsEmbed

ddragonBase = "http://ddragon.leagueoflegends.com/cdn/10.25.1"
ddragonBaseIcon = f"{ddragonBase}/img/profileicon/"

maxDisplayLeaderboard = 5


class InHouse(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.mongoClient = MongoClient(
            f"mongodb+srv://Dueces:{os.getenv('MONGOPASSWORD')}@cluster0-mzmgc.mongodb.net/test?retryWrites=true&w=majority")
        self.cacheControl = utils.CacheControl.CacheControl()
        self.commandMap = {
            'win': (self.calculateGeneralWinStats, True),
            'loss': (self.calculateGeneralWinStats, False),
            'dpm': (self.calculateGeneralDPMStats, None),
            'dpg': (self.calculateGeneralDPGStats, None),
            'topgpm': (self.calculateGeneralGPMStats, True),
            'botgpm': (self.calculateGeneralGPMStats, False),
            'cspm': (self.calculateGeneralCSPMStats, None),
            'kills': (self.calculateGeneralKDAStats, 'kills'),
            'deaths': (self.calculateGeneralKDAStats, 'deaths'),
            'assists': (self.calculateGeneralKDAStats, 'assists'),
            'avgkills': (self.calculateGeneralAverageKDAStats, 'kills'),
            'avgdeaths': (self.calculateGeneralAverageKDAStats, 'deaths'),
            'avgassists': (self.calculateGeneralAverageKDAStats, 'assists'),
            'topavgvisionscore': (self.calculateGeneralVisionScoreStats, True),
            'botavgvisionscore': (self.calculateGeneralVisionScoreStats, False),
            'topvspm': (self.calculateVisionScorePerMinute, True),
            'botvspm': (self.calculateVisionScorePerMinute, False),
            'topuniquechampions': (self.calculateUniqueChampionStats, True),
            'botuniquechampions': (self.calculateUniqueChampionStats, False),
            'topkp': (self.calculateAverageKillParticipation, True),
            'botkp': (self.calculateAverageKillParticipation, False),
            'ban': (self.calculateBanStats, None),
            'pick': (self.calculatePickStats, None),
            'presence': (self.calculatePresence, None),
            'topgames': (self.calculateGameCount, None),
            'topgoldshare': (self.calculateGoldShareStats, True),
            'botgoldshare': (self.calculateGoldShareStats, False),
            'general': (self.calculateGeneralLeagueStats, None)
        }

    @commands.Cog.listener()
    async def on_ready(self):
        print("Inhouse Command Ready")

    @commands.command(aliases=["inhousehelp"])
    async def inHouseHelp(self, ctx):
        embed = await generateInHouseHelpEmbed(self.commandMap.keys())
        await ctx.send(embed=embed)

    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.command(aliases=["leaderboards", "lb", "leaderboard", "stats"])
    async def calculateInHouseStats(self, ctx, option):

        # if not botUtil.isVexrax(ctx.message.author.id):
        #     await ctx.send("Maintenance mode enabled, Database is dead")
        #     return

        if option.lower() in self.commandMap:
            if self.commandMap[option.lower()][1] is None:
                embed = await self.commandMap[option.lower()][0]()
            else:
                embed = await self.commandMap[option.lower()][0](self.commandMap[option.lower()][1])
        else:
            embed = await self.generatePlayerStats(option)

        await ctx.send(embed=embed)
        return

    @commands.has_any_role('Admin', 'GALAXY BRAIN')
    @commands.command()
    async def addMatchForInHouseStats(self, ctx, username):

        # if not botUtil.isVexrax(ctx.message.author.id):
        #     await ctx.send("Due to rate limits/API keys please get vexrax to run this command")
        #     return

        try:

            db = self.mongoClient["Skynet"]
            collection = db["InHouses"]

            encryptedId = await self.cacheControl.getEncryptedSummonerId(username)

            if encryptedId == "":
                await ctx.send(f"Encrypted Summoner Id retured bad error code, check if API key is valid")
                return
            summonerObj = await self.cacheControl.getLiveMatch(encryptedId)
            if summonerObj is None:
                await ctx.send(f"{username} is not in a match")
                return

            # Logic for checking if its a valid inhouse
            if summonerObj["gameType"] != "CUSTOM_GAME" or summonerObj["gameMode"] != "CLASSIC":
                await ctx.send(f"{summonerObj['gameId']} is not a correct custom match, not adding to DB")
                return
            if len(summonerObj["participants"]) != 10:
                await ctx.send(
                    f"{summonerObj['gameId']} does not have enough players to be added to the inhouse stats, amount of players {len(summonerObj['participants'])}. Not adding to the DB")
                return
            document = collection.find_one({"gameId": summonerObj['gameId']})
            if document is not None:
                await ctx.send(f"{summonerObj['gameId']} is already in the DB, not adding")
                return

            # If execution gets to this point, then its a valid match. Add it to the DB
            participantMap = {}
            for summoner in summonerObj['participants']:
                participantMap[str(summoner['championId'])] = str(summoner['summonerName'])

            addedBy = ctx.message.author.name + ctx.message.author.discriminator
            finalDict = {'matchId': summonerObj['gameId'], 'addedBy': addedBy, "gameData": participantMap}
            collection.insert_one(finalDict)

            championMap = {}
            championKeyMap = await self.cacheControl.getChampionKeyMap()
            for key in participantMap:
                championMap[championKeyMap[key]] = participantMap[key]

            embedmatch = await generateMatchEmbed(summonerObj['gameId'], championMap)
            await ctx.send(embed=embedmatch)
        except Exception as e:
            await ctx.send(f"Something went wrong {e} ")
            return

    @commands.command()
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
            return discord.Embed(title=f"Summoner Not Found", description=f"FYI: Names are case sensitive",
                                 color=discord.Color.dark_red())
        playerIconId = await self.cacheControl.getSummonerIcon(summonerName)
        embed = await generateEmbedForPlayerStats(summonerName, playerStats, f"{ddragonBaseIcon}{playerIconId}.png")
        return embed

    async def calculateGeneralWinStats(self, highest):
        sortedDict = await self.generateLeaderboardDict('averagePercent', highest, 'win', 'totalGames')
        lbName = "Top 5"
        if not highest:
            lbName = "Bottom 5"
        return generateLeaderboardEmbed(sortedDict, f"{lbName} Winrate players",
                                        f"Out of {len(sortedDict)} players, these players have the {lbName} winrate")

    async def calculateGeneralDPMStats(self):
        sortedDict = await self.generateLeaderboardDict('averageGameTime', True, 'totalDamageDealtToChampions',
                                                        'totalGameTime')
        return generateLeaderboardEmbed(sortedDict, "Top 5 DPM players",
                                        "DPM is a statistic that calculates your average damage per minute")

    async def calculateGeneralGPMStats(self, sortAcending):
        sortedDict = await self.generateLeaderboardDict('averageGameTime', sortAcending, 'goldEarned', 'totalGameTime')
        lbName = "Top 5"
        if not sortAcending:
            lbName = "Bottom 5"
        return generateLeaderboardEmbed(sortedDict, f"{lbName} GPM players", "Gold Per Minute")

    async def calculateGeneralDPGStats(self):
        sortedDict = await self.generateLeaderboardDict('average', True, 'totalDamageDealtToChampions', 'goldEarned')
        return generateLeaderboardEmbed(sortedDict, "Top 5 DPG players",
                                        "DPG is a statistic that shows how well a given player uses the gold they are given")

    async def calculateGeneralCSPMStats(self):
        sortedDict = await self.generateLeaderboardDict('multiaddaverageGameTime', True, 'totalMinionsKilled',
                                                        'neutralMinionsKilled', 'totalGameTime')
        return generateLeaderboardEmbed(sortedDict, "Top 5 CS/M players", "Just CS per Min")

    async def calculateGeneralKDAStats(self, type):
        sortedDict = await self.generateLeaderboardDict('single', True, type)
        return generateLeaderboardEmbed(sortedDict, f"Top 5 {type} players",
                                        f"Highest total {type} count in the league")

    async def calculateAverageKillParticipation(self, highest):
        sortedDict = await self.generateLeaderboardDict('summedAvg', highest, 'kills', 'assists', 'totalKillsAvailable')
        lbName = "Top 5"
        if not highest:
            lbName = "Bottom 5"
        return generateLeaderboardEmbed(sortedDict, f"{lbName} KP players", f"Kill Participation count in the league")

    async def calculateGeneralVisionScoreStats(self, highest):
        sortedDict = await self.generateLeaderboardDict('average', highest, 'visionScore', 'totalGames')
        lbName = "Top"
        if not highest:
            lbName = "Bottom"
        return generateLeaderboardEmbed(sortedDict, f"{lbName} 5 Average Vision Score players", f"Cool Stats")

    async def calculateGameCount(self):
        sortedDict = await self.generateLeaderboardDict('single', True, 'totalGames')
        return generateLeaderboardEmbed(sortedDict, f"Top 5 game count players", f"Cool Stats")

    async def calculateVisionScorePerMinute(self, highest):
        sortedDict = await self.generateLeaderboardDict('averageGameTime', highest, 'visionScore', 'totalGameTime')
        lbName = "Top"
        if not highest:
            lbName = "Bottom"
        return generateLeaderboardEmbed(sortedDict, f"{lbName} 5 Vision Score Per Minute Players",
                                        f"This stats tells us how good of a warder you are")

    async def calculateGeneralAverageKDAStats(self, type):
        sortedDict = await self.generateLeaderboardDict('average', True, type, 'totalGames')
        return generateLeaderboardEmbed(sortedDict, f"Top 5 Average {type} players",
                                        f"Highest average {type} count in the league")

    async def calculateUniqueChampionStats(self, highest):
        uniques = await self.cacheControl.getStats('unique')
        sortedDict = sorted(uniques.items(), key=operator.itemgetter(1), reverse=highest)
        lbName = "Top"
        if not highest:
            lbName = "Bottom"
        return generateLeaderboardEmbed(sortedDict, f"{lbName} 5 players by unique champions ",
                                        f"Unique champions played in inhouse Matches")

    async def calculateBanStats(self):
        data = await self.cacheControl.getStats('ban')
        sortedDict = sorted(data.items(), key=operator.itemgetter(1), reverse=True)
        return generateLeaderboardEmbed(sortedDict, "Highest Ban Champions", "These are the most banned champions")

    async def calculatePickStats(self):
        data = await self.cacheControl.getStats('pick')
        sortedDict = sorted(data.items(), key=operator.itemgetter(1), reverse=True)
        return generateLeaderboardEmbed(sortedDict, "Highest Pick Champions", "These are the most picked champions")

    async def calculateGoldShareStats(self, highest):
        sortedDict = await self.generateLeaderboardDict('averagePercent', highest, 'goldEarned', 'totalGoldAvailable')
        lbName = "Top 5"
        if not highest:
            lbName = "Bottom 5"
        return generateLeaderboardEmbed(sortedDict, f"{lbName} gold share players",
                                        f"This stat tells us what your average % of your teams total gold")

    async def calculateGeneralLeagueStats(self):
        leagueDict = await self.generateGeneralLeagueStatsDict()
        db = self.mongoClient["Skynet"]
        collection = db["InHouses"]
        matchCount = collection.find().count()
        return await generateGeneralStatsEmbed(leagueDict, matchCount)

    async def calculatePresence(self):
        bans = Counter(await self.cacheControl.getStats('ban'))
        picks = Counter(await self.cacheControl.getStats('pick'))
        presence = bans + picks
        db = self.mongoClient["Skynet"]
        collection = db["InHouses"]
        matchCount = collection.find().count()
        for key in presence:
            presence[key] = round(presence[key] / matchCount, 2)
        sortedDict = sorted(presence.items(), key=operator.itemgetter(1), reverse=True)
        return generateLeaderboardEmbed(sortedDict, "Highest Presence Champions",
                                        "These are the champions that were picked or banned the most")

    async def generateLeaderboardDict(self, type, sortDecending, *argv):
        playersData = await self.cacheControl.getStats('general')
        db = self.mongoClient["Skynet"]
        collection = db["InHouses"]
        matchCount = collection.find().count()
        minRequiredGames = int(round(matchCount * 0.1))
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
                    LeaderBoardDict[key] = round(
                        (playersData[key][argv[0]] + playersData[key][argv[1]]) / (playersData[key][argv[2]] / 60), 2)
                elif type == "summedAvg":
                    LeaderBoardDict[key] = round(
                        (playersData[key][argv[0]] + playersData[key][argv[1]]) / (playersData[key][argv[2]]), 2)

        return sorted(LeaderBoardDict.items(), key=operator.itemgetter(1), reverse=sortDecending)

    async def generateGeneralLeagueStatsDict(self):
        playersData = await self.cacheControl.getStats('general')
        leagueSummedStats = Counter({})
        for player in playersData:
            leagueSummedStats.update(Counter(playersData[player]))
        return leagueSummedStats


async def setup(client):
    await client.add_cog(InHouse(client))
