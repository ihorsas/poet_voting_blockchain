import json
import time
from hashlib import sha256

from src.blockchain.transaction import Transaction


class Block:
    def __init__(self, transactions, previous_hash, wait_time, timestamp: float = None, hash: str = None):
        self.timestamp = time.time() if timestamp is None else timestamp
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.wait_time = wait_time
        self.hash = self.calculate_hash() if hash is None else hash

    def calculate_hash(self):
        block_string = json.dumps(self.hash_data(), sort_keys=True).encode()
        return sha256(block_string).hexdigest()

    def hash_data(self):
        return {
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'wait_time': self.wait_time,
            'previous_hash': self.previous_hash,
        }

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'wait_time': self.wait_time,
            'hash': self.hash,
        }

    @classmethod
    def from_dict(cls, dict_):
        return cls(
            transactions=[Transaction.from_dict(tx) for tx in dict_['transactions']],
            previous_hash=dict_['previous_hash'],
            wait_time=dict_['wait_time'],
            timestamp=dict_['timestamp'],
            hash=dict_['hash']
        )