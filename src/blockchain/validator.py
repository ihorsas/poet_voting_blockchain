import random
import threading

from src.blockchain.block import Block


class Validator:
    def __init__(self, address: str):
        self.address = address
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

    def validate_block(self, block: Block):
        if not self.block_to_add:
            self.block_to_add = block
            self.start_wait_timer()

    def __repr__(self):
        return f"Validator {self.address}"

    def to_dict(self):
        return {
            "address": self.address,
            "wait_time": self.wait_time,
            "block_to_add": self.block_to_add,
            "validated_blocks": [block.to_dict() for block in self.validated_blocks],
        }

    @classmethod
    def from_dict(cls, dict_):
        obj = cls(dict_["address"])
        obj.validated_blocks = [Block.from_dict(block) for block in dict_["chain"]]
        obj.wait_time = dict_["wait_time"]
        obj.block_to_add = dict_["block_to_add"]
        return obj
