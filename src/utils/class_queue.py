from collections import deque


class Queue(deque):
    def __init__(self):
        super().__init__()

    def enqueue(self, r):
        self.append(r)

    def dequeue(self):
        if not self.is_empty():
            return self.popleft()

    def is_empty(self):
        return len(self) == 0
    
