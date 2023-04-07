from collections import deque


class Stack(deque):
    def __init__(self):
        super().__init__()

    def push(self, r):
        self.append(r)

    def pop(self):
        if not self.is_empty():
            return super().pop()

    def is_empty(self):
        return len(self) == 0
    
