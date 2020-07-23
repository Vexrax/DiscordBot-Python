import discord
import random
from discord.ext import commands

class CopyPasta(commands.Cog):

    pastas =  [
        "If Earleking has million number of fans i am one of them. if Earleking has ten fans i am one of them. if Earleking has no fans. that means i am no more on the earth. if world against Earleking , i am against the world. i love Earleking till my last breath... die hard fan of Earleking . Hit like if u think Earleking best & smart in the world",
        "Earleking makes: \n my rod needlessly large \n my wand blast \n my phantom dance \n my cannon rapidly fire \n my tome amplify \n my hydra ravenous \n my spellbook unseal",
        "Earleking fired up his stream for another day of soloQ, but foolishly forgot to check if Vexrax was in a game. He opened up Vexrax’s stream to find him sitting in queue… He frantically began tabbing between his client and Vexrax’s stream, then one after the other… both queues popped. “I need the toilet” he said to his chat. He ran to the wall and unplugged his internet. He was safe for another day."
    ]

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        print("CopyPasta Command Ready")

    @commands.command()
    async def copypasta(self, ctx):
        for pasta in self.pastas:
            await ctx.send(pasta)

def setup(client):
    client.add_cog(CopyPasta(client))