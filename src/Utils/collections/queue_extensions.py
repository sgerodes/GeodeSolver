import heapq
from typing import Callable, Any


class PrioritySet:
    def __init__(self):
        self.heap = []
        self.set = set()

    def add(self, d, pri):
        if d not in self.set:
            heapq.heappush(self.heap, (pri, d))
            self.set.add(d)

    def get(self):
        pri, d = heapq.heappop(self.heap)
        self.set.remove(d)
        return d

    def recompute_all(self, key: Callable[[Any], Any]):
        old_set = self.set
        self.heap = []
        self.set = set()

        for item in old_set:
            self.add(item, key(item))

    def __len__(self) -> int:
        return len(self.heap)
