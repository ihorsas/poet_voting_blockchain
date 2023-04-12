import random
import threading

from rsa import PublicKey

from src.blockchain.block import Block
from src.p2p.peer import Peer


class Validator:
    def __init__(self, public_key: PublicKey, address: Peer):
        self.public_key = public_key
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
            self.wait_time = None

    def generate_wait_time(self):
        self.wait_time = random.randint(1, 10)  # Random wait time between 1-10 seconds

    def set_wait_time(self, wait_time):
        self.wait_time = wait_time

    def add_seconds_to_wait_time(self, seconds):
        self.wait_time += seconds

    def add_block(self):
        if self.block_to_add:
            self.validated_blocks.append(self.block_to_add)
            self.block_to_add = None

    def validate_block(self, block: Block):
        if not self.block_to_add:
            self.block_to_add = block
            self.start_wait_timer()

    def __repr__(self):
        return f"Validator {self.public_key}"

    def to_dict(self):
        return {
            "public_key": self.public_key.save_pkcs1().hex(),
            "address": self.address.to_dict(),
            "wait_time": self.wait_time,
            "block_to_add": self.block_to_add.to_dict() if self.block_to_add else None,
            "validated_blocks": [block.to_dict() for block in self.validated_blocks],
        }

    @classmethod
    def from_dict(cls, dict_):
        public_key = PublicKey.load_pkcs1(bytes.fromhex(dict_['public_key']))
        address = Peer.from_dict(dict_['address'])
        obj = cls(public_key, address)
        obj.validated_blocks = [Block.from_dict(block) for block in dict_["validated_blocks"]]
        obj.wait_time = dict_["wait_time"]
        obj.block_to_add = Block.from_dict(dict_["block_to_add"]) if dict_["block_to_add"] else None
        return obj
