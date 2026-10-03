import random

class MusicQueue:
    def __init__(self):
        self.queue = []
        self.current = None
        self.autoplay = False

    def add(self, song):
        self.queue.append(song)

    def next(self):
        if len(self.queue) > 0:
            self.current = self.queue.pop(0)
            return self.current
        self.current = None
        return None

    def clear(self):
        self.queue.clear()

    def remove(self, index: int):
        if 0 <= index < len(self.queue):
            return self.queue.pop(index)
        return None

    def move(self, from_idx: int, to_idx: int):
        if 0 <= from_idx < len(self.queue) and 0 <= to_idx < len(self.queue):
            song = self.queue.pop(from_idx)
            self.queue.insert(to_idx, song)
            return True
        return False

    def shuffle(self):
        random.shuffle(self.queue)