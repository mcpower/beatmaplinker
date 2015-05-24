from collections import deque


class LimitedSet(set):
    """A set which has a maximum length.

    Once it reaches the maximum length, the oldest key will be removed.
    Retains most of the time complexity of a set.
    """
    def __init__(self, maxlen=None, iterable=None):
        if iterable is None:
            set.__init__(self)
            self.queue = deque()
        else:
            truncated = list(iterable)[-maxlen:]
            set.__init__(self, truncated)
            self.queue = deque(truncated)
        self.maxlen = maxlen

    def add(self, key):
        if key not in self:
            if len(self) == self.maxlen:
                set.remove(self, self.queue.popleft())
            set.add(self, key)
            self.queue.append(key)

    def remove(self, key):
        set.remove(self, key)
        self.queue.remove(key)

    def discard(self, key):
        if key in self:
            self.remove(key)

    def pop(self):
        out = self.queue.pop()
        set.remove(self, out)
        return out

    def clear(self):
        set.clear(self)
        self.queue.clear()
