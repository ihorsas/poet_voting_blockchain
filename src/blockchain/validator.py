import threading
import time
import random

class Validator:
    def __init__(self, id):
        self.id = id
        self.wait_time = None
        self.wait_timer = None
        self.block_to_add = None
        self.validated_blocks = []

    def start_wait_timer(self):
        self.wait_timer = threading.Timer(self.wait_time, self.add_block)
        self.wait_timer.start()

    def stop_wait_timer(self):
        if self.wait_timer:
            self.wait_timer.cancel()

    def set_wait_time(self):
        self.wait_time = random.randint(1, 10)  # Random wait time between 1-10 seconds

    def add_block(self):
        if self.block_to_add:
            self.validated_blocks.append(self.block_to_add)
            self.block_to_add = None

    def validate_block(self, block):
        if not self.block_to_add:
            self.block_to_add = block
            self.start_wait_timer()

    def __repr__(self):
        return f"Validator {self.id}"