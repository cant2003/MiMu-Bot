import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

#! Carga de variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

#!Permisos / eventos del bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

#!Crear cliente de discord
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"MiMu está conectado como {bot.user}")
    
    try: 
        await bot.load_extension("cogs.music")
        await bot.load_extension("cogs.ai")
        print("Cog de Música cargado correctamente.")
    except Exception as e:
        print(f"Error al cargar cogs: {e}")
    
    try:
        await bot.tree.sync()
        print("Comandos slash sincronizados.")
    except Exception as e:
        print(e)
bot.run(TOKEN)