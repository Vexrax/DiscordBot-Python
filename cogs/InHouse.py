import os

from discord.ext import commands
from pymongo import MongoClient
import requests
import discord


import json

riotAPIBase = "https://na1.api.riotgames.com"
APIKEY = 'RGAPI-a6b7577f-8047-4954-95aa-853c60f855e5' #DEV API key expires daily

class InHouse(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.mongoClient = MongoClient(f"mongodb+srv://Dueces:{os.getenv('MONGOPASSWORD')}@cluster0-mzmgc.mongodb.net/test?retryWrites=true&w=majority")

    @commands.Cog.listener()
    async def on_ready(self):
        print("Quote Command Ready")

    @commands.command()
    async def calculateInHouseStats(self, ctx, option):
        db = self.mongoClient["Skynet"]
        collection = db["InHouses"]
        GamesData = {}
        for document in collection.find():
            didTeam100win = False
            matchData = requests.get(f'{riotAPIBase}/lol/match/v4/matches/{document["matchId"]}?api_key={APIKEY}').json()
            for team in matchData["teams"]:
                if team['teamId'] == 100:
                    didTeam100win = (team['win'] == 'Win')

            for player in matchData['participants']:
                name = document['gameData'][str(player["championId"])]
                if (player['teamId'] == 100 and didTeam100win) or (player['teamId'] == 200 and not didTeam100win):
                    if name in GamesData:
                        GamesData[name]['Win'] += 1
                    else:
                        GamesData[name] = {
                            'Win': 1,
                            'Loss':0
                        }
                else:
                    if name in GamesData:
                        GamesData[name]['Loss'] += 1
                    else:
                        GamesData[name] = {
                            'Win': 0,
                            'Loss':1
                        }
        embed = discord.Embed( title="WINNERS", description=f"BIG Ws", color=discord.Color.dark_purple())
        for key in GamesData:
            embed.add_field(name=key, value=f"{ round(GamesData[key]['Win'] / (GamesData[key]['Win'] + GamesData[key]['Loss']), 2) * 100}% Winrate Wins: {GamesData[key]['Win']}, Loss: {GamesData[key]['Loss']}")
        await ctx.send(embed=embed)
        return

    @commands.command()
    async def addMatchForInHouseStats(self, ctx):
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
def setup(client):
    client.add_cog(InHouse(client))