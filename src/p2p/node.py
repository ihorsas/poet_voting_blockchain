from src.block import Block
from src.blockchain import Blockchain
from src.transaction import Transaction


class Node:
    def __init__(self, blockchain: Blockchain, peers):
        self.blockchain = blockchain
        self.peers = peers

    def add_peer(self, peer):
        self.peers.add(peer)

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
            return True

    def mine_block(self):
        if not self.blockchain.pending_transactions:
            return None
        block = self.blockchain.mine_block()
        return block

    def sync_blockchain(self, blockchain: Blockchain):
        if len(blockchain.chain) > len(self.blockchain.chain):
            self.blockchain.chain = blockchain.chain
        elif len(blockchain.chain) == len(self.blockchain.chain):
            for tx in blockchain.pending_transactions:
                if tx not in self.blockchain.pending_transactions:
                    self.blockchain.add_transaction(tx)

    def broadcast(self, message_type, message):
        for peer in self.peers:
            self.send_message(peer, message_type, message)

    def send_message(self, peer, message_type, message):
        # TODO: Implement sending of message to peer
        pass