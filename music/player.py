from music.queue import SongQueue

class MusicPlayer:
    def __init__(self):
        self.queues = {}

    def get_queue(self, guild_id: int):
        if guild_id not in self.queues:
            self.queues[guild_id] = SongQueue()
        return self.queues[guild_id]

# Instancia global para usar en los cogs
guild_players = MusicPlayer()