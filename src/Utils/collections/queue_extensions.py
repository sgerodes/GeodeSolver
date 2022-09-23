import heapq


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
