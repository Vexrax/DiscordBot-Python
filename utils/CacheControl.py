import os

from discord.ext import commands
from pymongo import MongoClient
import requests
import discord
import utils.Util as botUtil
from collections import Counter
import time

riotAPIBase = "https://na1.api.riotgames.com"
APIKEY = '' #DEV API key expires daily

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
