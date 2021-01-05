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
    embed.add_field(name="Vision Score Per Min", value=f"{round((playerStats['visionScore']) / totalGameTime, 2)}", inline=True)

    embed.add_field(name="XP Diff at 10", value=f"{round((xpDiffs['0-10'] * 10 )/ gameCount, 2)}", inline=True)
    embed.add_field(name="Gold Diff at 10", value=f"{round((goldDiffs['0-10'] * 10) / gameCount, 2)}", inline=True)
    embed.add_field(name="CS Diff at 10", value=f"{round((csDiffs['0-10'] * 10) / gameCount, 2)}", inline=True)

    embed.add_field(name="XP Diff at 20", value=f"{round(((xpDiffs['0-10'] * 10 ) + (xpDiffs['10-20'] * 10 )) / gameCount, 2)}", inline=True)
    embed.add_field(name="Gold Diff at 20", value=f"{round(((goldDiffs['0-10'] * 10) + (goldDiffs['10-20'] * 10)) / gameCount, 2)}", inline=True)
    embed.add_field(name="CS Diff at 20", value=f"{round(((csDiffs['0-10'] * 10) + (csDiffs['10-20'] * 10)) / gameCount, 2)}", inline=True)

    return embed