import logging
from threading import Lock
from typing import Dict

import rsa

from src.blockchain.block import Block
from src.blockchain.contract_methods import ContractMethods
from src.blockchain.smart_contract import VotingSmartContract
from src.blockchain.status import Status
from src.blockchain.transaction import Transaction
from src.p2p.validator import Validator

logging.basicConfig(level=logging.DEBUG)


class Blockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]
        self.pending_transactions = list()
        self.contracts: Dict[str, VotingSmartContract] = {}
        self.lock = Lock()

    def create_genesis_block(self) -> Block:
        return Block([], "0", 0)

    def add_block(self, block: Block, validator: Validator) -> bool:
        if block in validator.validated_blocks:
            if self.is_valid_block(block, self.last_block):
                self.lock.acquire()
                try:
                    if self.is_valid_block(block, self.last_block):  # Check again after acquiring lock
                        self.chain.append(block)
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
            if self.need_new_block():
                return True, Status.NEW_BLOCK
            return True, Status.NEW_TRANSACTION
        return False, Status.IGNORED

    def need_new_block(self) -> bool:
        if len(self.pending_transactions) >= 5:
            return True
        return False

    def get_new_block(self) -> Block:
        return Block(self.pending_transactions, self.last_block.hash)

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
            message = f"{tx.voter_key.save_pkcs1().hex()}{tx.contract_name}{tx.contract_method}{tx.args}{tx.timestamp}".encode()
            try:
                rsa.verify(message, tx.signature, public_key)
            except Exception as e:
                logging.exception(e)
                return False
        return True

    def add_existing_block(self, block: Block):
        if self.is_valid_block(block, self.last_block):
            self.chain.append(block)
            return True
        return False

    def add_existing_contract(self, contract: VotingSmartContract):
        self.contracts[contract.name] = contract

    def execute_contracts(self):
        for tx in self.last_block.transactions:
            if tx.contract_method == ContractMethods.CREATE:
                contract = VotingSmartContract(tx.contract_name)
                if contract in self.contracts:
                    logging.debug(f"Contract {contract} already exists")
                    continue
                self.contracts[contract.name] = contract
                logging.debug(f"Contract {contract} added to blockchain during block creation")
            current_contract = self.get_contract_by_name(tx.contract_name)
            if current_contract is not None:
                try:
                    if tx.contract_method == ContractMethods.START_VOTING:
                        current_contract.start_voting()
                        logging.debug(f"Contract {current_contract.name} started during block creation")
                    if tx.contract_method == ContractMethods.ADD_CANDIDATE:
                        current_contract.add_candidate(*tx.args)
                        logging.debug(
                            f"Candidate {tx.args} added to contract {current_contract.name} during block creation")
                    if tx.contract_method == ContractMethods.VOTE:
                        current_contract.vote(*tx.args)
                        logging.debug(f"Vote added to contract {current_contract.name} during block creation")
                    if tx.contract_method == ContractMethods.FINISH_VOTING:
                        current_contract.finish_voting()
                        logging.debug(f"Contract {current_contract.name} finished during block creation")
                except Exception as e:
                    logging.exception(e)

    def get_contract_by_name(self, contract_name) -> VotingSmartContract:
        return self.contracts.get(contract_name)

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
            "pending_transactions": [tx.to_dict() for tx in self.pending_transactions],
            "contracts": {name: self.contracts[name].to_dict() for name in self.contracts}
        }

    @classmethod
    def from_dict(cls, dict_):
        obj = cls()
        obj.chain = [Block.from_dict(block) for block in dict_["chain"]]
        obj.pending_transactions = [Transaction.from_dict(tx) for tx in dict_["pending_transactions"]]
        contracts_dict = dict_["contracts"]
        obj.contracts = {name: VotingSmartContract.from_dict(contracts_dict[name]) for name in contracts_dict}
        return obj

    def copy(self):
        new_chain = Blockchain()
        new_chain.chain = self.chain.copy()
        new_chain.pending_transactions = self.pending_transactions.copy()
        return new_chain

    @property
    def last_block(self):
        return self.chain[-1]

    def is_valid_transaction(self, tx: Transaction) -> bool:
        try:
            tx_signed = tx.signature is not None
            if tx.contract_method == ContractMethods.CREATE:
                return tx_signed and not self.is_contract_exist(tx.contract_name)
            if tx.contract_method == ContractMethods.START_VOTING:
                return tx_signed and self.is_contract_exist(tx.contract_name) and not self.is_contract_started(
                    tx.contract_name)
            if tx.contract_method == ContractMethods.ADD_CANDIDATE:
                return tx_signed and self.is_contract_exist(tx.contract_name) and \
                       not self.is_contract_started(tx.contract_name) \
                       and not self.is_candidate_exist(tx.contract_name, tx.args[0])
            if tx.contract_method == ContractMethods.VOTE:
                return tx_signed and self.is_contract_exist(tx.contract_name) and \
                       self.is_contract_started(tx.contract_name) and \
                       self.is_candidate_exist(tx.contract_name, tx.args[1]) and not self.is_voter_voted_already(
                    tx.voter_key, tx.contract_name)
            if tx.contract_method == ContractMethods.FINISH_VOTING:
                return tx_signed and self.is_contract_exist(tx.contract_name) and self.is_contract_started(
                    tx.contract_name) and not self.is_contract_finished(tx.contract_name)
        except Exception as e:
            logging.exception(e)
            return False

    def is_contract_exist(self, contract_name):
        pending_contracts = [tx.contract_name for tx in self.pending_transactions if
                             tx.contract_method == ContractMethods.CREATE]
        if contract_name in pending_contracts or contract_name in self.contracts:
            logging.debug(f"Contract {contract_name} exists")
            return True
        logging.debug(f"Contract {contract_name} does not exist")
        return False

    def is_contract_started(self, contract_name):
        started_pending_contracts = [tx.contract_name for tx in self.pending_transactions if
                                     tx.contract_method == ContractMethods.START_VOTING]
        contract = self.get_contract_by_name(contract_name)
        if contract_name in started_pending_contracts or (contract.is_voting_in_progress() if contract else False):
            logging.debug(f"Contract {contract_name} is already started")
            return True
        logging.debug(f"Contract {contract_name} is not started")
        return False

    def is_candidate_exist(self, contract_name, candidate):
        pending_candidates = [tx.args[0] for tx in self.pending_transactions if
                              tx.contract_method == ContractMethods.ADD_CANDIDATE and tx.contract_name == contract_name]
        contract = self.get_contract_by_name(contract_name)
        if candidate in pending_candidates or (contract.is_candidate_exist(candidate) if contract else False):
            logging.debug(f"Candidate {candidate} is already exist for {contract_name}")
            return True
        logging.debug(f"Candidate {candidate} does not exist for {contract_name}")
        return False

    def is_voter_voted_already(self, voter_key, contract_name):
        pending_votes = [tx.voter_key for tx in self.pending_transactions if
                         tx.contract_method == ContractMethods.VOTE and tx.contract_name == contract_name]
        contract = self.get_contract_by_name(contract_name)
        if voter_key in pending_votes or (contract.is_voter_key_exist(voter_key) if contract else False):
            logging.debug(f"Voter {voter_key} is already voted for {contract_name}")
            return True
        logging.debug(f"Voter {voter_key} did not vote yet for {contract_name}")
        return False

    def is_contract_finished(self, contract_name):
        finished_pending_contracts = [tx.contract_name for tx in self.pending_transactions if
                                      tx.contract_method == ContractMethods.FINISH_VOTING]
        contract = self.get_contract_by_name(contract_name)
        if contract_name in finished_pending_contracts or (contract.is_voting_in_finished() if contract else False):
            logging.debug(f"Contract {contract_name} is already finished")
            return True
        logging.debug(f"Contract {contract_name} is not finished yet")
        return False

    def get_candidates_for_contract(self, contract_name):
        pending_candidates = [tx.args[0] for tx in self.pending_transactions if
                              tx.contract_method == ContractMethods.ADD_CANDIDATE and tx.contract_name == contract_name]
        contract = self.get_contract_by_name(contract_name)
        if contract is not None:
            pending_candidates += contract.candidates.keys()
        return pending_candidates
