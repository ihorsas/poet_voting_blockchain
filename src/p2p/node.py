from src.blockchain.block import Block
from src.blockchain.blockchain import Blockchain
from src.blockchain.status import Status
from src.blockchain.transaction import Transaction


class Node:
    def __init__(self, blockchain: Blockchain, peers):
        self.blockchain = blockchain
        self.peers = peers

    def add_peer(self, peer):
        self.peers.append(peer)

    def remove_peer(self, peer):
        self.peers.remove(peer)

    def add_transaction(self, transaction: Transaction):
        if transaction not in self.blockchain.pending_transactions:
            self.blockchain.add_transaction(transaction)
            return True
        else:
            return False

    def add_block(self, block: Block):
        if self.blockchain.is_valid_block(block, self.blockchain.chain[-1]):
            self.blockchain.add_block(block)
            self.update_transactions(block)
            return True

    def sync_blockchain(self, blockchain: Blockchain):
        if len(blockchain.chain) > len(self.blockchain.chain):
            self.blockchain.chain = blockchain.chain
            self.blockchain.pending_transactions = [tx for tx in self.blockchain.pending_transactions if
                                                    tx not in blockchain.chain[-1].transactions]
        if len(blockchain.chain) == len(self.blockchain.chain):
            for tx in blockchain.pending_transactions:
                if tx not in self.blockchain.pending_transactions:
                    result, status = self.blockchain.add_transaction(tx)
                    if result and status == Status.NEW_BLOCK:
                        return True
        return False

    def update_transactions(self, block):
        for tx in block.transactions:
            if tx in self.blockchain.pending_transactions:
                self.blockchain.pending_transactions.remove(tx)
