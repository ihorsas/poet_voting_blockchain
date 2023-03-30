import logging
from threading import Lock
from typing import Dict

import rsa

from src.blockchain.block import Block
from src.blockchain.smart_contract import VotingSmartContract
from src.blockchain.status import Status
from src.blockchain.transaction import Transaction
from src.blockchain.validator import Validator

logging.basicConfig(level=logging.DEBUG)


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = list()
        self.validators = []
        self.register_validator(Validator("init_validator"))
        self.contracts: Dict[str, VotingSmartContract] = {}
        self.lock = Lock()

    def create_genesis_block(self) -> Block:
        return Block([], "0", 0)

    def register_validator(self, validator: Validator):
        for v in self.validators:
            if v.address == validator.address:
                return False, 0
        self.validators.append(validator)
        if validator.wait_time is None:
            validator.set_wait_time()
        return True, validator.wait_time

    def remove_validator(self, validator: Validator):
        self.validators.remove(validator)

    def add_block(self, block: Block) -> bool:
        elapsed_times = [v.wait_time for v in self.validators]
        min_elapsed_time = min(elapsed_times)
        min_elapsed_time_idx = elapsed_times.index(min_elapsed_time)
        validator = self.validators[min_elapsed_time_idx]
        if block in validator.validated_blocks:
            if self.is_valid_block(block, self.last_block):
                self.lock.acquire()
                try:
                    if self.is_valid_block(block, self.last_block):  # Check again after acquiring lock
                        self.chain.append(block)
                        for v in self.validators:
                            v.stop_wait_timer()
                            v.set_wait_time()
                        return True
                finally:
                    self.lock.release()
        return False

    def add_transaction(self, transaction: Transaction, private_key=None):
        if private_key is not None:
            transaction.sign(private_key)
        if self.is_valid_transaction(transaction):
            if transaction not in self.pending_transactions:
                self.pending_transactions.append(transaction)
            if self.add_block_if_needed():
                return True, Status.NEW_BLOCK
            return True, Status.NEW_TRANSACTION
        return False, Status.IGNORED

    def add_block_if_needed(self) -> bool:
        if len(self.pending_transactions) >= 2:
            block = Block(self.pending_transactions, self.last_block.hash)
            for v in self.validators:
                v.validate_block(block)
            while not self.add_block(block):
                pass
            self.execute_contracts()
            self.pending_transactions = []
            return True
        return False

    @staticmethod
    def is_valid_block(block: Block, previous_block: Block) -> bool:
        if previous_block.hash != block.previous_hash:
            return False

        block_hash = block.calculate_hash()

        if block_hash != block.hash:
            return False

        # Verify all transactions in the block
        for tx in block.transactions:
            # Verify the signature of the transaction
            public_key = tx.voter_key
            message = f"{tx.voter_key.save_pkcs1().hex()}{tx.candidate}{tx.contract}{tx.timestamp}".encode()
            try:
                rsa.verify(message, tx.signature, public_key)
            except Exception as e:
                logging.exception(e)
                return False
        return True

    def add_existing_block(self, block: Block):
        self.chain.append(block)

    def add_existing_contract(self, contract: VotingSmartContract):
        self.contracts[contract.name] = contract

    def deploy_contract(self, contract: VotingSmartContract) -> bool:
        if contract in self.contracts:
            return False
        self.contracts[contract.name] = contract
        return True

    def execute_contracts(self):
        for tx in self.pending_transactions:
            current_contract = self.get_contract_by_name(tx.contract)
            if current_contract is not None:
                try:
                    current_contract.vote(tx.voter_key, tx.candidate)
                except Exception as e:
                    logging.exception(e)

    def add_candidate_to_contract(self, contract_name: str, candidate: str) -> bool:
        try:
            self.contracts.get(contract_name).add_candidate(candidate)
        except Exception as e:
            logging.exception(e)
            return False
        return True

    def get_contract_by_name(self, contract_name) -> VotingSmartContract:
        return self.contracts.get(contract_name)

    def start_voting(self, contract_name) -> bool:
        if self.get_contract_by_name(contract_name) is not None:
            self.get_contract_by_name(contract_name).start_voting()
            return True
        else:
            return False

    def finish_voting(self, contract_name) -> bool:
        if self.get_contract_by_name(contract_name) is not None:
            self.get_contract_by_name(contract_name).finish_voting()
            return True
        else:
            return False

    def get_results(self, contract_name):
        try:
            return self.get_contract_by_name(contract_name).get_results()
        except Exception as e:
            logging.exception(e)
        return []

    def get_winner(self, contract_name):
        try:
            return self.get_contract_by_name(contract_name).get_winner()
        except Exception as e:
            logging.exception(e)
        return []

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

    @property
    def last_block(self):
        return self.chain[-1]

    def is_valid_transaction(self, transaction: Transaction) -> bool:
        contract = self.get_contract_by_name(transaction.contract)
        pending_votes = [tx.voter_key for tx in self.pending_transactions]

        return transaction.signature is not None and contract.is_candidate_exist(transaction.candidate) and \
               (not contract.is_voter_key_exist(transaction.voter_key)) and transaction.voter_key not in pending_votes \
               and contract.is_voting_in_progress()
