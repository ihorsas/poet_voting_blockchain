import hashlib
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
        self.wait_time = random.randint(1, 5)  # Random wait time between 1-5 seconds

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


class Blockchain:
    def __init__(self):
        self.chain = [Block(1, [], 0, "0")]
        self.current_transactions = []
        self.validators = []
        self.register_validator(Validator(1))
        self.register_validator(Validator(2))

    def register_validator(self, validator):
        self.validators.append(validator)
        if validator.wait_time is None:
            validator.set_wait_time()

    def remove_validator(self, validator):
        self.validators.remove(validator)

    def add_block(self, block):
        elapsed_times = [v.wait_time for v in self.validators]
        min_elapsed_time = min(elapsed_times)
        min_elapsed_time_idx = elapsed_times.index(min_elapsed_time)
        validator = self.validators[min_elapsed_time_idx]
        if block in validator.validated_blocks:
            self.chain.append(block)
            for v in self.validators:
                v.stop_wait_timer()
                v.set_wait_time()
            return True
        return False

    def add_transaction(self, transaction):
        self.current_transactions.append(transaction)
        if len(self.current_transactions) == 5:
            block = Block(len(self.chain), self.current_transactions, time.time(), self.chain[-1].hash)
            for v in self.validators:
                v.validate_block(block)
            while not self.add_block(block):
                pass
            self.current_transactions = []
            return True
        return False


class Block:
    def __init__(self, index, transactions, timestamp, previous_hash):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self):
        return hashlib.sha256(str(self.index).encode() +
                              str(self.transactions).encode() +
                              str(self.timestamp).encode() +
                              str(self.previous_hash).encode()).hexdigest()


# Create a new blockchain
blockchain = Blockchain()

# Add some transactions to the blockchain
blockchain.add_transaction("Alice sends 0.01 BTC to Bob")
blockchain.add_transaction("Bob sends 0.05 BTC to Charlie")
blockchain.add_transaction("Charlie sends 0.02 BTC to Alice")
blockchain.add_transaction("Ihor sends 0.02 BTC to Alice")
blockchain.add_transaction("Michael sends 0.02 BTC to Alice")

# Print the current state of the blockchain
print(blockchain.chain)