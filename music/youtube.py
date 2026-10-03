import os
import asyncio
import discord
import yt_dlp

coockies_path = os.path.join(os.getcwd(), "cookies.txt")

ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

if os.path.exists(coockies_path):
    ytdl_format_options['cookiefile'] = coockies_path

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('webpage_url')
        self.duration = data.get('duration', 0)  # en segundos
        self.uploader = data.get('uploader', 'Desconocido')
        self.thumbnail = data.get('thumbnail')
        self.requester = requester

    @classmethod
    async def create_source(cls, search: str, requester, *, loop: asyncio.AbstractEventLoop = None):
        loop = loop or asyncio.get_running_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(search, download=False))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data.get('url')
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, requester=requester)