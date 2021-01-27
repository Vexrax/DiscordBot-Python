import discord

maxDisplayLeaderboard = 5

def generateLeaderboardEmbed(sortedDict, title, subtitle):
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
        if i == maxDisplayLeaderboard:
            return embed

    return embed


async def generateEmbedForPlayerStats(summonerName, playerDataDict, iconLink):

    gameCount = playerDataDict["gameCount"]
    playerStats = playerDataDict["playerStats"]
    totalGameTime = playerDataDict["totalGameTime"]
    csDiffs = playerDataDict["csDiffs"]
    goldDiffs = playerDataDict["goldDiffs"]
    xpDiffs = playerDataDict["xpDiffs"]
    champions = playerDataDict["champions"]
    lastTenWR = playerDataDict["lastTenWR"]

    embed = discord.Embed(title=f"{summonerName}'s InHouse Stats", description=f"Cool Stats", color=discord.Color.dark_blue())
    embed.set_thumbnail(url=iconLink)
    embed.set_author(name=summonerName, icon_url=iconLink)
    embed.add_field(name="Games Played", value=f"{gameCount}")
    embed.add_field(name="Win Rate", value=f"{round(playerStats['win'] / gameCount, 2) * 100}%")
    embed.add_field(name="Last 10 Games Win Rate", value=f"{lastTenWR}%")

    embed.add_field(name="Damage Per Gold", value=f"{round(playerStats['totalDamageDealtToChampions'] / playerStats['goldEarned'], 2)}", inline=True)
    embed.add_field(name="Damage Per Minute", value=f"{round(playerStats['totalDamageDealtToChampions'] / totalGameTime, 2)}", inline=True )
    embed.add_field(name="Unique Champions", value=f"{len(champions.keys())}")

    embed.add_field(name="Average Kills Per Game", value=f"{round(playerStats['kills'] / gameCount, 2)}", inline=True)
    embed.add_field(name="Average Deaths Per Game", value=f"{round(playerStats['deaths'] / gameCount, 2)}", inline=True)
    embed.add_field(name="Average Assists Per Game", value=f"{round(playerStats['assists'] / gameCount, 2)}", inline=True)

    embed.add_field(name="Objective Damage Per Game", value=f"{round(playerStats['damageDealtToObjectives'] / gameCount, 2)}", inline=True)
    embed.add_field(name="Turrets Killed", value=f"{playerStats['turretKills']}" , inline=True)
    embed.add_field(name="\u200B", value="\u200B")

    embed.add_field(name="CS per min", value=f"{round((playerStats['totalMinionsKilled'] + playerStats['neutralMinionsKilled']) / totalGameTime, 2)}", inline=True)
    embed.add_field(name="Average Vision Score", value=f"{round((playerStats['visionScore']) / gameCount, 2)}", inline=True)
    embed.add_field(name="Vision Score Per Min", value=f"{round((playerStats['visionScore']) / totalGameTime, 2)}", inline=True)

    embed.add_field(name="XP Diff at 10", value=f"{round((xpDiffs['0-10'] * 10 )/ gameCount, 2)}", inline=True)
    embed.add_field(name="Gold Diff at 10", value=f"{round((goldDiffs['0-10'] * 10) / gameCount, 2)}", inline=True)
    embed.add_field(name="CS Diff at 10", value=f"{round((csDiffs['0-10'] * 10) / gameCount, 2)}", inline=True)

    embed.add_field(name="XP Diff at 20", value=f"{round(((xpDiffs['0-10'] * 10 ) + (xpDiffs['10-20'] * 10 )) / gameCount, 2)}", inline=True)
    embed.add_field(name="Gold Diff at 20", value=f"{round(((goldDiffs['0-10'] * 10) + (goldDiffs['10-20'] * 10)) / gameCount, 2)}", inline=True)
    embed.add_field(name="CS Diff at 20", value=f"{round(((csDiffs['0-10'] * 10) + (csDiffs['10-20'] * 10)) / gameCount, 2)}", inline=True)

    championValueStrs = ["", "", ""]
    champsPerColums = int(len(champions.keys()) / 3) + 1
    currentColumn = 0
    i = 0
    for key in champions:
        wr = round((champions[key]['win'] / champions[key]['games'])*100, 1)
        championValueStrs[currentColumn] += f"{key} ({champions[key]['games']}):\n```{getWinrateColor(wr)}\n{wr}% WR``` \n"
        i += 1
        if not i < champsPerColums:
            i = 0
            currentColumn += 1

    if(championValueStrs[0] == ""):
        championValueStrs[0] = "\u200B"
    if (championValueStrs[1] == ""):
        championValueStrs[1] = "\u200B"
    if (championValueStrs[2] == ""):
        championValueStrs[2] = "\u200B"

    embed.add_field(name="Champions Played:", value=f"{championValueStrs[0]}", inline=True)
    embed.add_field(name="\u200B", value=f"{championValueStrs[1]}", inline=True)
    embed.add_field(name="\u200B", value=f"{championValueStrs[2]}", inline=True)

    return embed


async def generateInHouseHelpEmbed(commandList):
    keyPerRow = int(len(commandList) / 3) + 1
    currentColumn = 0
    i = 0
    strArr = ["Options:\n", "Options:\n", "Options:\n"]
    for key in commandList:
        strArr[currentColumn] += f"{key}\n"
        i += 1
        if not i < keyPerRow:
            i = 0
            currentColumn += 1

    embed = discord.Embed(title="In House Commands", description="Commands for the inhouse bot",
                          color=discord.Color.dark_teal())
    embed.add_field(name=f"//leaderboard", value=f"{strArr[0]}")
    embed.add_field(name=f"\u200B", value=f"{strArr[1]}")
    embed.add_field(name=f"\u200B", value=f"{strArr[2]}")

    embed.add_field(name=f"//stats", value=f"Options:\nSummoner Name (Case sensitive)")
    embed.add_field(name=f"\u200B", value=f"\u200B")
    embed.add_field(name=f"\u200B", value=f"\u200B")
    return embed

async def generateMatchEmbed(matchId, playerDict):
    embed = discord.Embed(title=f"{matchId} Live Right Now", description=f"Season 1 of In Houses", color=discord.Color.dark_green())
    list = [(k, v) for k, v in playerDict.items()]
    i = 0
    try:
        while i < 5:
            embed.add_field(name=f"{list[i][1]}", value=f"{list[i][0]}")
            embed.add_field(name="\u200B", value="\u200B")
            embed.add_field(name=f"{list[i+5][1]}", value=f"{list[i+5][0]}")
            i+=1
    except:
        embed = discord.Embed(title=f"{matchId} Live Right Now", description=f"Season 1 of In Houses",
                              color=discord.Color.dark_green())
    return embed

async def generateGeneralStatsEmbed(summedDict, matchCount):
    embed = discord.Embed(title=f"The KFC Season 1 Invitational", description=f"Season 1 of In Houses", color=discord.Color.dark_orange())
    embed.set_thumbnail(url="https://ddragon.leagueoflegends.com/cdn/10.25.1/img/profileicon/3379.png") # Chicken Icon

    embed.add_field(name="Games Played", value=f"{matchCount}")
    embed.add_field(name="Total Damage", value=f"{summedDict['totalDamageDealtToChampions']}")
    embed.add_field(name="\u200B", value="\u200B")

    embed.add_field(name="Total Kills", value=f"{summedDict['kills']}")
    embed.add_field(name="Total Deaths", value=f"{summedDict['deaths']}")
    embed.add_field(name="Total Assists", value=f"{summedDict['assists']}")

    embed.add_field(name="Total Physical Damage", value=f"{summedDict['physicalDamageDealtToChampions']}")
    embed.add_field(name="Total Magic Damage", value=f"{summedDict['magicDamageDealtToChampions']}")
    embed.add_field(name="Total True Damage", value=f"{summedDict['trueDamageDealtToChampions']}")

    embed.add_field(name="Total Gold Earned", value=f"{summedDict['goldEarned']}")
    embed.add_field(name="Total Gold Spent", value=f"{summedDict['goldSpent']}")
    embed.add_field(name="\u200B", value="\u200B")

    embed.add_field(name="Total Turret Kills", value=f"{summedDict['turretKills']}")
    embed.add_field(name="Total Inhib Kills", value=f"{summedDict['inhibitorKills']}")
    embed.add_field(name="Total Damage To Objectives", value=f"{summedDict['damageDealtToObjectives']}")

    embed.add_field(name="Total CS", value=f"{summedDict['totalMinionsKilled'] + summedDict['neutralMinionsKilled']}")
    embed.add_field(name="Wards Placed", value=f"{summedDict['wardsPlaced']}")
    embed.add_field(name="Wards Killed", value=f"{summedDict['wardsKilled']}")

    return embed

def getWinrateColor(winrate):
    if winrate > 60:
        return "yaml"
    return ""
