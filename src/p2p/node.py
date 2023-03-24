from src.blockchain.block import Block
from src.blockchain.blockchain import Blockchain
from src.blockchain.smart_contract import VotingSmartContract, State
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
            result, status = self.blockchain.add_transaction(transaction)
            if result and status == Status.NEW_BLOCK:
                return True
        return False

    def add_block(self, block: Block):
        if self.blockchain.is_valid_block(block, self.blockchain.chain[-1]):
            self.blockchain.add_existing_block(block)
            self.update_transactions(block)
            return True
        return False

    def sync_blockchain(self, blockchain: Blockchain):
        result = False
        if len(blockchain.contracts) > len(self.blockchain.contracts):
            self.blockchain.contracts = blockchain.contracts
            result = True

        if len(blockchain.chain) > len(self.blockchain.chain):
            self.blockchain.chain = blockchain.chain
            self.blockchain.pending_transactions = [tx for tx in self.blockchain.pending_transactions if
                                                    tx not in blockchain.chain[-1].transactions]
            self.blockchain.contracts = blockchain.contracts
            result = True

        if len(blockchain.chain) == len(self.blockchain.chain):
            for tx in blockchain.pending_transactions:
                if tx not in self.blockchain.pending_transactions:
                    result, status = self.blockchain.add_transaction(tx)
                    if result and status == Status.NEW_BLOCK:
                        result = True
        return result

    def update_transactions(self, block):
        for tx in block.transactions:
            if tx in self.blockchain.pending_transactions:
                self.blockchain.pending_transactions.remove(tx)

    def add_contract(self, contract: VotingSmartContract):
        if self.blockchain.get_contract_by_name(contract.name) is None:
            self.blockchain.add_existing_contract(contract)
            return True
        return False

    def add_candidate(self, contract_name, candidate):
        self.blockchain.add_candidate_to_contract(contract_name, candidate)

    def update_state(self, contract_name, state):
        contract = self.blockchain.get_contract_by_name(contract_name)
        if state == State.IN_PROGRESS and contract.state == State.NOT_STARTED:
            self.blockchain.start_voting(contract_name)
        elif state == State.FINISHED and contract_name != State.FINISHED:
            self.blockchain.finish_voting(contract_name)
