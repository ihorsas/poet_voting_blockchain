import logging
from typing import List

from src.blockchain.block import Block
from src.blockchain.blockchain import Blockchain
from src.blockchain.smart_contract import VotingSmartContract
from src.blockchain.status import Status
from src.blockchain.transaction import Transaction
from src.p2p.peer import Peer
from src.p2p.validator import Validator


class Node:
    def __init__(self, blockchain: Blockchain, peers: List[Peer], validators: List[Validator]):
        self.blockchain = blockchain
        self.peers = peers
        self.validators = validators
        self.local_validator: Validator = None

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
            if self.blockchain.add_existing_block(block):
                self.blockchain.execute_contracts()
                self.update_transactions(block)
                return True
        logging.info(f"Wasn't able to add block {block.to_dict()} to blockchain")
        return False

    def sync_blockchain(self, blockchain: Blockchain):
        result = False
        if len(blockchain.contracts) > len(self.blockchain.contracts):
            self.blockchain.contracts = blockchain.contracts
            result = True

        if len(blockchain.chain) > len(self.blockchain.chain):
            self.blockchain.chain = blockchain.chain
            self.blockchain.pending_transactions = [tx for tx in self.blockchain.pending_transactions if
                                                    tx not in blockchain.last_block.transactions]
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

    def validate_block(self, block):
        self.local_validator.validate_block(block)
        if self.is_blockchain_has_block(block):
            logging.info(f"Block {block.to_dict()} is already in blockchain")
            self.stop_wait_timers()
            return False
        while not self.blockchain.add_block(block, self.local_validator):
            if self.is_blockchain_has_block(block):
                logging.info(f"Block {block.to_dict()} is already in blockchain")
                self.stop_wait_timers()
                return False
        self.stop_wait_timers()
        self.blockchain.execute_contracts()
        self.update_transactions(block)
        return True

    def is_blockchain_has_block(self, block: Block):
        return self.blockchain.last_block.hash == block.hash

    def register_validator(self, validator: Validator):
        for v in self.validators:
            if v.address == validator.address:
                return False
        self.local_validator = validator
        self.validators.append(validator)
        return True

    def add_validator(self, validator: Validator):
        for v in self.validators:
            if v.address == validator.address:
                return False
        self.validators.append(validator)
        return True

    def generate_wait_time_for_local_validator(self):
        self.local_validator.generate_wait_time()
        return self.local_validator.wait_time

    def add_wait_time_for_validator(self, wait_time, address):
        for v in self.validators:
            if v.address == address:
                v.set_wait_time(wait_time)
                return True
        return False

    def increase_wait_time_for_validator(self, time):
        for v in self.validators:
            v.add_seconds_to_wait_time(time)

    def are_all_validators_have_wait_time(self, min_time=0):
        for v in self.validators:
            if v.wait_time is None:
                return False
            if v.wait_time <= min_time:
                return False
        return True

    def stop_wait_timers(self):
        for v in self.validators:
            v.stop_wait_timer()
