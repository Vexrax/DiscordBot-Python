import os
import time
from collections import Counter

from pymongo import MongoClient
import requests

riotAPIBase = "https://na1.api.riotgames.com"
APIKEY = '' #DEV API key expires daily
cdragonChampionBase = f" https://cdn.communitydragon.org/10.25.1/champion"

'''
Interacts with the MONGO Database and the RIOT api. Decides wether to go to the DB for data or to RIOT for data (Kinda a cache but not really)
'''
class CacheControl:

    def __init__(self):
        self.mongoClient = MongoClient(f"mongodb+srv://Dueces:{os.getenv('MONGOPASSWORD')}@cluster0-mzmgc.mongodb.net/test?retryWrites=true&w=majority")

    async def getMatchReport(self, matchId):
        db = self.mongoClient["Skynet"]
        collection = db["Matches"]
        document = collection.find_one({"gameId": matchId})
        if not document is None:
            return document
        data = requests.get(f'{riotAPIBase}/lol/match/v4/matches/{matchId}?api_key={APIKEY}').json()
        collection.insert_one(data)
        return data

    async def getStats(self, type):
        db = self.mongoClient["Skynet"]
        collection = db["Stats"]
        document = collection.find_one({'id': type})


        if (document is not None) and (time.time() <= (document['creationTime'] + 30*60)):
            return document['stats']
        else:
            if type == 'general':
                stats = await self.aggregateStatsForEveryone()
            elif type == 'ban':
                stats = await self.aggregateStatsForEveryone()
            elif type == 'unique':
                stats = await self.aggregateUniqueChampionStats()
            elif type == 'pick':
                stats = await self.aggregatePickStats()
            else:
                stats = await self.aggregateStatsForPlayer(type)
            collection.delete_one({'id': type})
            collection.insert_one({'id': type, 'stats': stats, 'creationTime': time.time()})
            return stats

    async def getEncryptedSummonerId(self, summonerName):
        summonerObj = requests.get(f'{riotAPIBase}/lol/summoner/v4/summoners/by-name/{summonerName}?api_key={APIKEY}').json()
        return summonerObj["id"]

    async def getSummonerIcon(self, summonerName):
        summonerObj = requests.get(f'{riotAPIBase}/lol/summoner/v4/summoners/by-name/{summonerName}?api_key={APIKEY}').json()
        return summonerObj["profileIconId"]

    async def getLiveMatch(self, encryptedSummonerId):
        summonerObj = requests.get(f'{riotAPIBase}/lol/spectator/v4/active-games/by-summoner/{encryptedSummonerId}?api_key={APIKEY}').json()
        return summonerObj

    async def aggregateUniqueChampionStats(self):
        db = self.mongoClient["Skynet"]
        collection = db["InHouses"]
        playerChampionDict = {}
        for document in collection.find():
            for championId in document['gameData'].keys():
                if document['gameData'][championId] not in playerChampionDict:
                    playerChampionDict[document['gameData'][championId]] = set()
                playerChampionDict[document['gameData'][championId]].add(int(championId))

        uniques = {}
        for key in playerChampionDict:
            uniques[key] = len(playerChampionDict[key])

        return uniques

    async def aggregateBanStats(self):

        db = self.mongoClient["Skynet"]
        collection = db["InHouses"]

        championBanDict = {}
        championDataDict = {}

        for document in collection.find():
            matchData = await self.getMatchReport(document["matchId"])
            for team in matchData['teams']:
                for ban in team['bans']:
                    if str(ban['championId']) not in championDataDict:
                        data = requests.get(f"{cdragonChampionBase}/{ban['championId']}/data").json()
                        championDataDict[str(ban['championId'])] = data
                    data = championDataDict[str(ban['championId'])]
                    if data['name'] not in championBanDict:
                        championBanDict[data['name']] = 0
                    championBanDict[data['name']] += 1
        return championBanDict

    async def aggregateStatsForEveryone(self):
        db = self.mongoClient["Skynet"]
        collection = db["InHouses"]
        playersData = {}
        for document in collection.find():
            matchData = await self.getMatchReport(document["matchId"])
            totalBlueKillsInMatch = 0
            totalRedKillsInMatch = 0
            for player in matchData['participants']:
                name = document['gameData'][str(player["championId"])]
                stats = Counter(player["stats"])
                if name not in playersData:
                    playersData[name] = Counter({})
                    playersData[name]['totalGameTime'] = 0
                    playersData[name]['totalGames'] = 0
                    playersData[name]['totalKillsAvailable'] = 0
                playersData[name] = playersData[name] + stats
                playersData[name]['totalGameTime'] += matchData["gameDuration"]
                playersData[name]['totalGames'] += 1

                if player['participantId'] <= 5:
                    totalBlueKillsInMatch += stats['kills']
                else:
                    totalRedKillsInMatch += stats['kills']

            # Needs to happen after all the paricipants have been run thru
            for player in matchData['participants']:
                name = document['gameData'][str(player["championId"])]
                if player['participantId'] <= 5:
                    playersData[name]['totalKillsAvailable'] += totalBlueKillsInMatch
                else:
                    playersData[name]['totalKillsAvailable'] += totalRedKillsInMatch

        return playersData

    async def aggregateStatsForPlayer(self, playername):
        db = self.mongoClient["Skynet"]
        mongoMatchCollection = db["InHouses"]
        gameIds = {}
        for document in mongoMatchCollection.find():
            for key in document['gameData']:
                if document['gameData'][key] == playername:
                    gameIds[document['matchId']] = key

        if len(gameIds.keys()) == 0:
            return {}

        playerStats = Counter({})

        goldDiffs = Counter({})
        xpDiffs = Counter({})
        csDiffs = Counter({})

        gameCount = 0
        totalGameTime = 0
        championsInfo = {}

        for matchId in gameIds:
            matchData = await self.getMatchReport(matchId)
            statsForMatch = Counter(self.findStatsFromParticipantList(matchData['participants'], gameIds[matchId]))
            diffsForMatch = self.generatePlayerDiffsFromMatch(matchData['participants'], gameIds[matchId])

            goldDiffs.update(diffsForMatch["goldPerMinDeltas"])
            xpDiffs.update(diffsForMatch["xpPerMinDeltas"])
            csDiffs.update(diffsForMatch["creepsPerMinDeltas"])
            playerStats = statsForMatch + playerStats

            if gameIds[matchId] not in championsInfo:
                championsInfo[gameIds[matchId]] = Counter({'win': 0, 'games': 0})
            championsInfo[gameIds[matchId]].update(Counter({'win': statsForMatch['win'], 'games': 1}))

            gameCount += 1
            totalGameTime += int(matchData['gameDuration'] / 60)

        return {
            'gameCount' : gameCount,
            'playerStats': playerStats,
            'totalGameTime': totalGameTime,
            'csDiffs': csDiffs,
            'goldDiffs': goldDiffs,
            'xpDiffs': xpDiffs,
            'champions': self.convertChampionIdsKeysToNames(championsInfo)
        }

    async def aggregatePickStats(self):
        db = self.mongoClient["Skynet"]
        collection = db["InHouses"]

        champCountDict = {}
        championDataDict = {}

        for document in collection.find():
            for champion in document['gameData'].keys():
                if str(champion) not in championDataDict:
                    data = requests.get(f"{cdragonChampionBase}/{champion}/data").json()
                    championDataDict[str(champion)] = data['name']
                name = championDataDict[str(champion)]

                if name not in champCountDict:
                    champCountDict[name] = 0

                champCountDict[name] += 1

        return champCountDict

    def findStatsFromParticipantList(self, participantList, targetChampion):
        for champStats in participantList:
            if(str(champStats['championId']) == targetChampion):
                return champStats['stats']
        return {}

    def convertChampionIdsKeysToNames(self, championIdDict):
        championDataDict = {}
        returnDict = {}
        for champion in championIdDict:
            if str(champion) not in championDataDict:
                data = requests.get(f"{cdragonChampionBase}/{champion}/data").json()
                championDataDict[str(champion)] = data['name']
            name = championDataDict[str(champion)]
            returnDict[name] = championIdDict[champion]
        return returnDict

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
            if champStats['participantId'] == lanePartnerParticipantId:

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