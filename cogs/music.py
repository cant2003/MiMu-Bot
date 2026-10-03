import discord
from discord import app_commands
from discord.ext import commands
from music.youtube import YTDLSource
from music.queue import MusicQueue
from cogs.ai import client, MODEL_ID, MIMU_SYSTEM_PROMPT

class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {} # Diccionario para manejar colas independientes por servidor (Guild ID)

    def get_queue(self, guild_id: int):
        if guild_id not in self.queues:
            self.queues[guild_id] = MusicQueue()
        return self.queues[guild_id]

    @app_commands.command(name="join", description="Ingresa al canal de voz actual.")
    async def join(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ ¡Debes estar en un canal de voz!", ephemeral=True)
            return
        channel = interaction.user.voice.channel
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        await interaction.response.send_message(f"🔊 Conectado a **{channel.name}**.")

    @app_commands.command(name="play", description="Añade música a la cola o la reproduce de inmediato.")
    @app_commands.describe(busqueda="Nombre de la canción o enlace de YouTube")
    async def play(self, interaction: discord.Interaction, busqueda: str):
        if not interaction.user.voice:
            await interaction.response.send_message("❌ ¡Debes estar en un canal de voz!", ephemeral=True)
            return

        await interaction.response.defer()
        channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client

        if voice_client is None:
            voice_client = await channel.connect()
        elif voice_client.channel != channel:
            await voice_client.move_to(channel)

        server_queue = self.get_queue(interaction.guild.id)

        try:
            player = await YTDLSource.create_source(busqueda, requester=interaction.user, loop=self.bot.loop)
            
            if voice_client.is_playing() or voice_client.is_paused():
                server_queue.add(player)
                await interaction.followup.send(f"➕ Añadido a la cola: **{player.title}** (Pedida por {interaction.user.mention})")
            else:
                server_queue.current = player
                voice_client.play(player, after=lambda e: self.play_next(interaction.guild, voice_client))
                await interaction.followup.send(f"🎶 Reproduciendo ahora: **{player.title}** (Pedida por {interaction.user.mention})")
        except Exception as e:
            await interaction.followup.send(f"❌ Error al cargar la canción: `{e}`")

    def play_next(self, guild, voice_client):
        server_queue = self.get_queue(guild.id)
        next_song = server_queue.next()
        if next_song:
            voice_client.play(next_song, after=lambda e: self.play_next(guild, voice_client))
        elif server_queue.autoplay:
            # Si la cola está vacía pero el autoplay está activado, buscamos un tema aleatorio/relacionado
            self.bot.loop.create_task(self.trigger_autoplay(guild, voice_client))
        else:
            server_queue.current = None
    async def trigger_autoplay(self, guild, voice_client):
        server_queue = self.get_queue(guild.id)
        try:
            # Lista de canciones populares o aleatorias para el Autoplay por defecto
            canciones_azar = ["trending music hits", "anime openings music", "latin rock music", "kpop music hits", "jpop music hits", "electronic dance music"]
            import random
            busqueda_aleatoria = random.choice(canciones_azar)

            # Creamos el source de manera asíncrona
            player = await YTDLSource.create_source(busqueda_aleatoria, requester=self.bot.user, loop=self.bot.loop)
            server_queue.current = player
            
            # Reproducimos
            voice_client.play(player, after=lambda e: self.play_next(guild, voice_client))
            
            # Opcional: Enviar un mensaje al canal de texto avisando del autoplay si se desea
        except Exception as e:
            print(f"Error en Autoplay: {e}")

    @app_commands.command(name="pause", description="Pausa la canción actual.")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            await interaction.response.send_message("⏸️ Canción pausada.")
        else:
            await interaction.response.send_message("❌ No hay ninguna canción reproduciéndose.", ephemeral=True)

    @app_commands.command(name="resume", description="Reanuda la canción pausada.")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            await interaction.response.send_message("▶️ Canción reanudada.")
        else:
            await interaction.response.send_message("❌ El reproductor no está pausado.", ephemeral=True)

    @app_commands.command(name="skipe", description="Salta a la siguiente canción de la cola.")
    async def skipe(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop() # Esto activará automáticamente el evento after y pasará a la siguiente
            await interaction.response.send_message("⏭️ Canción saltada.")
        else:
            await interaction.response.send_message("❌ No hay nada reproduciéndose para saltar.", ephemeral=True)

    @app_commands.command(name="stop", description="Termina la transmisión y saca al bot del canal de voz.")
    async def stop(self, interaction: discord.Interaction):
        server_queue = self.get_queue(interaction.guild.id)
        server_queue.clear()
        vc = interaction.guild.voice_client
        if vc:
            await vc.disconnect()
            await interaction.response.send_message("🛑 Reproducción detenida y bot desconectado.")
        else:
            await interaction.response.send_message("❌ No estoy conectado a ningún canal.", ephemeral=True)

    @app_commands.command(name="volumen", description="Ajusta el nivel de volumen (1-100).")
    @app_commands.describe(nivel="Nivel de volumen entre 1 y 100")
    async def volumen(self, interaction: discord.Interaction, nivel: int):
        if not 1 <= nivel <= 100:
            await interaction.response.send_message("❌ El volumen debe estar entre 1 y 100.", ephemeral=True)
            return
        
        vc = interaction.guild.voice_client
        if vc and vc.source:
            vc.source.volume = nivel / 100.0
            await interaction.response.send_message(f"🔊 Volumen ajustado al **{nivel}%**.")
        else:
            await interaction.response.send_message("❌ No hay audio reproduciéndose actualmente.", ephemeral=True)

    @app_commands.command(name="list", description="Muestra la lista de canciones en espera y la actual.")
    async def list_queue(self, interaction: discord.Interaction):
        server_queue = self.get_queue(interaction.guild.id)
        if not server_queue.current and not server_queue.queue:
            await interaction.response.send_message("📭 La cola está vacía.", ephemeral=True)
            return

        desc = ""
        if server_queue.current:
            desc += f"**Reproduciendo ahora:**\n🎵 {server_queue.current.title} (Solicitado por {server_queue.current.requester.mention})\n\n"
        
        if server_queue.queue:
            desc += "**En espera:**\n"
            for i, song in enumerate(server_queue.queue, 1):
                desc += f"`{i}.` {song.title} (Por {song.requester.mention})\n"

        embed = discord.Embed(title="🎶 Cola de Reproducción", description=desc, color=discord.Color.blurple())
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="now", description="Muestra información detallada del tema actual.")
    async def now(self, interaction: discord.Interaction):
        server_queue = self.get_queue(interaction.guild.id)
        if not server_queue.current:
            await interaction.response.send_message("❌ No hay ninguna canción reproduciéndose.", ephemeral=True)
            return

        song = server_queue.current
        embed = discord.Embed(title="🎧 Reproduciendo Ahora", description=f"**[{song.title}]({song.url})**", color=discord.Color.green())
        embed.add_field(name="Canal / Artista", value=song.uploader, inline=True)
        embed.add_field(name="Solicitado por", value=song.requester.mention, inline=True)
        if song.thumbnail:
            embed.set_thumbnail(url=song.thumbnail)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="remove", description="Elimina un tema específico de la cola por su posición.")
    @app_commands.describe(posicion="Número de la posición en la cola")
    async def remove(self, interaction: discord.Interaction, posicion: int):
        server_queue = self.get_queue(interaction.guild.id)
        removed = server_queue.remove(posicion - 1)
        if removed:
            await interaction.response.send_message(f"🗑️ Eliminado de la cola: **{removed.title}**")
        else:
            await interaction.response.send_message("❌ Posición inválida en la cola.", ephemeral=True)

    @app_commands.command(name="clear", description="Borra toda la lista menos la canción actual.")
    async def clear(self, interaction: discord.Interaction):
        server_queue = self.get_queue(interaction.guild.id)
        server_queue.clear()
        await interaction.response.send_message("🧹 La cola ha sido limpiada (la canción actual sigue sonando).")

    @app_commands.command(name="shuffle", description="Mezcla aleatoriamente el orden de la cola.")
    async def shuffle(self, interaction: discord.Interaction):
        server_queue = self.get_queue(interaction.guild.id)
        if len(server_queue.queue) < 2:
            await interaction.response.send_message("❌ No hay suficientes canciones en la cola para mezclar.", ephemeral=True)
            return
        server_queue.shuffle()
        await interaction.response.send_message("🔀 ¡Cola mezclada aleatoriamente!")

    @app_commands.command(name="move", description="Mueve una canción de una posición a otra en la cola.")
    @app_commands.describe(origen="Posición actual de la canción", destino="Nueva posición deseada")
    async def move(self, interaction: discord.Interaction, origen: int, destino: int):
        server_queue = self.get_queue(interaction.guild.id)
        success = server_queue.move(origen - 1, destino - 1)
        if success:
            await interaction.response.send_message(f"🔄 Canción movida de la posición `{origen}` a `{destino}`.")
        else:
            await interaction.response.send_message("❌ Posiciones inválidas.", ephemeral=True)
            
    @app_commands.command(name="lyrics", description="Muestra la letra de la canción que está sonando actualmente.")
    async def lyrics(self, interaction: discord.Interaction):
        server_queue = self.get_queue(interaction.guild.id)
        if not server_queue.current:
            await interaction.response.send_message("❌ ¡No hay ninguna canción sonando para buscar su letra!", ephemeral=True)
            return

        await interaction.response.defer()
        cancion = server_queue.current.title

        prompt = (
            f"{MIMU_SYSTEM_PROMPT}\n\n"
            f"El usuario quiere la letra de la canción que está sonando: '{cancion}'. "
            f"Preséntala de manera ordenada y bonita para Discord, comentándola con tu entusiasmo musical."
        )

        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
            )
            texto_letra = response.text[:1900]
            embed = discord.Embed(title=f"📜 Letra: {cancion}", description=texto_letra, color=discord.Color.from_rgb(255, 105, 180))
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"❌ ¡Uf! No pude conseguir la letra: `{e}`")

    @app_commands.command(name="autoplay", description="Activa o desactiva la reproducción automática de canciones al azar.")
    async def autoplay(self, interaction: discord.Interaction):
        server_queue = self.get_queue(interaction.guild.id)
        server_queue.autoplay = not server_queue.autoplay
        estado = "activado 🟢 (¡Dejemos que el destino musical decida!)" if server_queue.autoplay else "desactivado 🔴"
        await interaction.response.send_message(f"✨ El modo **Autoplay** ha sido {estado}.")

async def setup(bot):
    await bot.add_cog(MusicCog(bot))