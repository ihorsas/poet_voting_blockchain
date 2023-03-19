import random
import time
from threading import Lock

import rsa

from src.block import Block
from src.transaction import Transaction


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = list()
        self.lock = Lock()

    def create_genesis_block(self):
        return Block([], "0", 0)

    def add_transaction(self, transaction, private_key=None):
        if private_key is not None:
            transaction.sign(private_key)
        if transaction.signature is not None:
            if transaction not in self.pending_transactions:
                self.pending_transactions.append(transaction)
                print(f"Transactions after adding {transaction.candidate} {[tx.to_dict() for tx in self.pending_transactions]}")

    def mine_block(self):
        previous_block = self.chain[-1]
        wait_time = random.randint(5, 10)  # Random wait time between 5 to 10 seconds
        print(f"Miner will wait for {wait_time} seconds before mining...")
        time.sleep(wait_time)  # Wait for the random time before mining
        start_time = time.time()  # Start the timer
        new_block = Block(self.pending_transactions, self.chain[-1].hash, wait_time)
        if self.is_valid_block(new_block, previous_block):
            self.lock.acquire()
            try:
                if self.is_valid_block(new_block, previous_block):  # Check again after acquiring lock
                    self.chain.append(new_block)
                    self.pending_transactions = []
                    print(f"Mined new block in {round(time.time() - start_time, 2)} seconds.")
                    return new_block
            finally:
                self.lock.release()
        else:
            print("Mined block is invalid. Discarding...")
            return None

    @staticmethod
    def is_valid_block(block, previous_block):
        if previous_block.hash != block.previous_hash:
            return False

        block_hash = block.calculate_hash()

        if block_hash != block.hash:
            return False

        # Verify all transactions in the block
        for tx in block.transactions:
            # Verify the signature of the transaction
            public_key = tx.voter_key
            message = f"{tx.voter_key.save_pkcs1().hex()}{tx.candidate}{tx.timestamp}".encode()
            try:
                rsa.verify(message, tx.signature, public_key)
            except Exception as e:
                print(f"Validation failed: {e}")
                return False
        return True

    def add_blockchain(self, blockchain):
        # merge existing blockchain with received from broadcast
        pass

    def add_block(self, block):
        self.chain.append(block)
        # add received block ahead of the existing blockchain
        pass

    def to_dict(self):
        return {
            "chain": [block.to_dict() for block in self.chain],
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions]
        }

    @classmethod
    def from_dict(cls, dict_):
        obj = cls()
        obj.chain = [Block.from_dict(block) for block in dict_["chain"]]
        obj.pending_transactions = [Transaction.from_dict(tx) for tx in dict_["pending_transactions"]]
        return obj

    def copy(self):
        new_chain = Blockchain()
        new_chain.chain = self.chain.copy()
        new_chain.pending_transactions = self.pending_transactions.copy()
        return new_chain