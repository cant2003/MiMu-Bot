import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from aiohttp import web

#! Carga de variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

#! Permisos / eventos del bot
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

#! Crear cliente de discord
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Mini servidor web para satisfacer a Render en el plan gratuito ---
async def handle(request):
    return web.Response(text="¡MiMu Bot está activo y sonando! 🎶💙")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle)
    runner = web.AppRunner(app)
    await runner.setup()
    
    # Render asigna automáticamente el puerto mediante la variable de entorno PORT
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Servidor web fantasma corriendo en el puerto {port}")

@bot.event
async def on_ready():
    print(f"MiMu está conectado como {bot.user}")
    
    # 1. Iniciamos el servidor web para Render
    bot.loop.create_task(start_web_server())
    
    # 2. Cargamos los cogs
    try: 
        await bot.load_extension("cogs.music")
        await bot.load_extension("cogs.ai")
        print("Cogs cargados correctamente.")
    except Exception as e:
        print(f"Error al cargar cogs: {e}")
    
    # 3. Sincronizamos los slash commands
    try:
        await bot.tree.sync()
        print("Comandos slash sincronizados.")
    except Exception as e:
        print(e)

bot.run(TOKEN)