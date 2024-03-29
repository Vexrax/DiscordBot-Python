import os
import time
from collections import Counter
import re
from pymongo import MongoClient
import pymongo
import requests

riotAPIBase = "https://na1.api.riotgames.com"
APIKEY = os.getenv('RIOT') #DEV API key expires daily
version = requests.get("https://ddragon.leagueoflegends.com/api/versions.json").json()[0]
cdragonChampionBase = f" https://cdn.communitydragon.org/{version}/champion"
ddragonBase = f"http://ddragon.leagueoflegends.com/cdn/{version}"


regex = re.compile('[^a-zA-Z]')

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
        response = requests.get(f'{riotAPIBase}/lol/match/v5/matches/{matchId}?api_key={APIKEY}')
        data = response.json()

        if response.status_code != 200:
            return data

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
                stats = await self.aggregateBanStats()
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
        response = requests.get(f'{riotAPIBase}/lol/summoner/v4/summoners/by-name/{summonerName}?api_key={APIKEY}')
        if response.status_code != 200:
            return ""
        summonerObj = response.json()
        return summonerObj["id"]

    async def getSummonerIcon(self, summonerName):
        response = requests.get(f'{riotAPIBase}/lol/summoner/v4/summoners/by-name/{summonerName}?api_key={APIKEY}')
        if response.status_code != 200:
            return ""
        summonerObj = response.json()
        return summonerObj["profileIconId"]

    async def getLiveMatch(self, encryptedSummonerId):
        response = requests.get(f'{riotAPIBase}/lol/spectator/v4/active-games/by-summoner/{encryptedSummonerId}?api_key={APIKEY}')
        if response.status_code != 200:
            return None
        return response.json()

    async def getChampionKeyMap(self):
        db = self.mongoClient["Skynet"]
        collection = db["Stats"]
        document = collection.find_one({'id': 'champKeyMap'})

        if (document is not None) and (document['version'] == version):
            return document['map']

        championKeyMap = {}
        cdnChampionJson = requests.get(f"{ddragonBase}/data/en_US/champion.json").json()["data"]
        for key in cdnChampionJson:
            championKey = cdnChampionJson[key]["key"]
            championKeyMap[championKey] = key

        collection.delete_one({'id': 'champKeyMap'})
        collection.insert_one({'id': 'champKeyMap', 'version': version, 'map': championKeyMap})
        return championKeyMap

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
        championDataDict = await self.getChampionKeyMap()

        for document in collection.find():
            matchData = await self.getMatchReport(document["matchId"])
            for team in matchData['teams']:
                for ban in team['bans']:
                    name = regex.sub('', championDataDict[str(ban['championId'])])
                    if name not in championBanDict:
                        championBanDict[name] = 0
                    championBanDict[name] += 1
        return championBanDict

    async def aggregateStatsForEveryone(self):
        db = self.mongoClient["Skynet"]
        collection = db["InHouses"]
        playersData = {}
        for document in collection.find():
            matchData = await self.getMatchReport(document["matchId"])

            # Match isnt ready, skip it
            if "gameId" not in matchData:
                continue

            totalBlueKillsInMatch, totalRedKillsInMatch, totalBlueGold, totalRedGold, = 0, 0, 0, 0
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
                    totalBlueGold += stats['goldEarned']
                else:
                    totalRedKillsInMatch += stats['kills']
                    totalRedGold += stats['goldEarned']


            # Needs to happen after all the paricipants have been run thru
            for player in matchData['participants']:
                name = document['gameData'][str(player["championId"])]
                if player['participantId'] <= 5:
                    playersData[name]['totalKillsAvailable'] += totalBlueKillsInMatch
                    playersData[name]['totalGoldAvailable'] += totalBlueGold
                else:
                    playersData[name]['totalKillsAvailable'] += totalRedKillsInMatch
                    playersData[name]['totalGoldAvailable'] += totalRedGold


        return playersData

    async def aggregateStatsForPlayer(self, playername):
        db = self.mongoClient["Skynet"]
        mongoMatchCollection = db["InHouses"]

        championKeyMap = await self.getChampionKeyMap()
        gameIds = {}

        # sort by -1 to get matches in order of insertion
        for document in mongoMatchCollection.find().sort("_id", -1):
            for key in document['gameData']:
                if document['gameData'][key] == playername:
                    gameIds[document['matchId']] = key

        if len(gameIds.keys()) == 0:
            return {}

        playerStats = Counter({})

        goldDiffs = Counter({})
        xpDiffs = Counter({})
        csDiffs = Counter({})
        roles = {}

        lastTenWR = 0

        gameCount = 0
        totalGameTime = 0
        championsInfo = {}

        for matchId in gameIds:
            matchData = await self.getMatchReport(matchId)

            # Match isnt ready, skip it
            if "gameId" not in matchData:
                continue

            statsForMatch = Counter(self.findStatsFromParticipantList(matchData['participants'], gameIds[matchId]))
            diffsForMatch = self.generatePlayerDiffsFromMatch(matchData['participants'], gameIds[matchId])

            goldDiffs.update(diffsForMatch["goldPerMinDeltas"])
            xpDiffs.update(diffsForMatch["xpPerMinDeltas"])
            csDiffs.update(diffsForMatch["creepsPerMinDeltas"])

            if diffsForMatch["role"] not in roles:
                roles[diffsForMatch["role"]] = Counter({'win': 0, 'games': 0})
            roles[diffsForMatch["role"]].update({'win': statsForMatch['win'], 'games': 1})

            playerStats = statsForMatch + playerStats

            if championKeyMap[gameIds[matchId]] not in championsInfo:
                championsInfo[championKeyMap[gameIds[matchId]]] = Counter({'win': 0, 'games': 0})
            championsInfo[championKeyMap[gameIds[matchId]]].update(Counter({'win': statsForMatch['win'], 'games': 1}))

            gameCount += 1
            if gameCount <= 10:
                lastTenWR = playerStats['win'] / gameCount

            totalGameTime += int(matchData['gameDuration'] / 60)

        return {
            'gameCount' : gameCount,
            'lastTenWR': round(lastTenWR, 2) * 100,
            'playerStats': playerStats,
            'totalGameTime': totalGameTime,
            'csDiffs': csDiffs,
            'goldDiffs': goldDiffs,
            'xpDiffs': xpDiffs,
            'champions': championsInfo,
            'roles': roles
        }

    async def aggregatePickStats(self):
        db = self.mongoClient["Skynet"]
        collection = db["InHouses"]

        champCountDict = {}
        championDataDict = await self.getChampionKeyMap()

        for document in collection.find():
            for champion in document['gameData'].keys():
                name = regex.sub('', championDataDict[str(champion)])
                if name not in champCountDict:
                    champCountDict[name] = 0
                champCountDict[name] += 1

        return champCountDict

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
                    "goldPerMinDeltas": gold,
                    "role": getRoleFromParticipantId(particpantId)
                }

def getRoleFromParticipantId(participantId):
    if participantId == 1 or participantId == 6:
        return 'TOP'
    elif participantId == 2 or participantId == 7:
        return 'JG'
    elif participantId == 3 or participantId == 8:
        return 'MID'
    elif participantId == 4 or participantId == 9:
        return 'BOT'
    else:
        return 'SUP'
