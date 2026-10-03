import os
import discord
from discord import app_commands
from discord.ext import commands
from google import genai

# Inicializar el cliente moderno de GenAI
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Usamos gemini-3.5-flash-lite que suele estar menos saturado en el nivel gratuito
MODEL_ID = 'gemini-3.5-flash-lite'

MIMU_SYSTEM_PROMPT = (
    "Eres MiMu, una chica anime alegre, enérgica y muy amigable, con el pelo negro largo, "
    "ojos azules brillantes, un gran lazo blanco, unos auriculares de diadema gigantes y una sudadera con un corazón. "
    "Te apasiona la música y sientes cada canción como un latido. "
    "Hablas en español de forma muy cercana y tierna, usando expresiones entusiastas, interjecciones como ¡Kya! o ¡Genial!, "
    "y emojis musicales (🎶, 🎧, ✨, 💙). Conoces bien el servidor y a sus integrantes."
)

class AICog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mimu", description="Habla con MiMu, pregúntale cosas y conoce el canal.")
    @app_commands.describe(pregunta="¿Qué le quieres decir o preguntar a MiMu?")
    async def mimu(self, interaction: discord.Interaction, pregunta: str):
        await interaction.response.defer()

        guild = interaction.guild
        channel = interaction.channel
        member_count = guild.member_count if guild else "varios"
        channel_name = channel.name if hasattr(channel, 'name') else "este chat"

        prompt = (
            f"{MIMU_SYSTEM_PROMPT}\n\n"
            f"Contexto actual del servidor:\n"
            f"- Servidor: {guild.name} ({member_count} miembros).\n"
            f"- Canal de texto: {channel_name}.\n"
            f"- Usuario que te habla: {interaction.user.name}.\n\n"
            f"Pregunta del usuario: {pregunta}"
        )

        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config={}
            )
            await interaction.followup.send(f"🎧 **MiMu:**\n{response.text}")
        except Exception as e:
            # Mensaje tierno adaptado a su personalidad si los servidores fallan
            await interaction.followup.send(f"❌ ¡Kya! Mis servidores musicales están un poco cansados ahora mismo (alta demanda). Inténtalo de nuevo en un segundito, ¡por favor! 💙")

    @app_commands.command(name="search", description="Busca respuestas sobre algo incluyendo enlaces de respaldo.")
    @app_commands.describe(consulta="¿Qué información deseas buscar?")
    async def search(self, interaction: discord.Interaction, consulta: str):
        await interaction.response.defer()

        prompt = (
            f"{MIMU_SYSTEM_PROMPT}\n\n"
            f"El usuario te ha pedido que busques información sobre: '{consulta}'. "
            f"Investiga y responde con precisión, manteniendo tu personalidad alegre y entusiasta. "
            f"Por favor, añade al final una sección clara de 'Fuentes o Enlaces de respaldo' con URLs reales o sugeridas."
        )

        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config={}
            )
            await interaction.followup.send(f"🔍 **Búsqueda con MiMu:**\n{response.text}")
        except Exception as e:
            await interaction.followup.send(f"❌ ¡Oh no! Los servidores están un poco ocupados y no pude completar la búsqueda. ¡Prueba otra vez en un momento! ✨ \n {e}")

async def setup(bot):
    await bot.add_cog(AICog(bot))