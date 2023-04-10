import time

from typing import Dict


class State:
    NOT_STARTED = "not_started"
    FINISHED = "finished"
    IN_PROGRESS = "in_progress"

class ContractMethods:
    CREATE = "create"
    ADD_CANDIDATE = "add_candidate"
    IS_CANDIDATE_EXIST = "is_candidate_exist"
    IS_VOTER_KEY_EXIST = "is_voter_key_exist"
    IS_VOTING_IN_PROGRESS = "is_voting_in_progress"
    VOTE = "vote"
    GET_RESULTS = "get_results"
    GET_WINNER = "get_winner"
    START_VOTING = "start_voting"
    FINISH_VOTING = "finish_voting"

class SmartContract:
    def __init__(self, unique_name: str):
        self.name = unique_name
        self.votes = {}
        self.candidates = {}
        self.state = State.NOT_STARTED

    def add_candidate(self, candidate: str):
        if candidate in self.candidates:
            raise Exception(f"{candidate} already exists.")
        self.candidates[candidate] = 0

    def is_candidate_exist(self, candidate: str) -> bool:
        return candidate in self.candidates

    def is_voter_key_exist(self, voter_key: str) -> bool:
        return voter_key in self.votes

    def is_voting_in_progress(self) -> bool:
        return self.state == State.IN_PROGRESS

    def vote(self, voter_key: str, candidate: str):
        if candidate not in self.candidates:
            raise Exception(f"{candidate} does not exist.")
        if voter_key in self.votes:
            raise Exception(f"Voter {voter_key} already voted.")
        if self.state == State.NOT_STARTED:
            raise Exception("Error: Voting period has not started yet.")
        if self.state == State.FINISHED:
            raise Exception("Error: Voting period has ended.")
        self.votes[voter_key] = candidate
        self.candidates[candidate] += 1

    def get_results(self):
        if self.state != State.FINISHED:
            raise Exception("Voting is not finished yet")
        return self.candidates

    def get_winner(self) -> str:
        if self.state != State.FINISHED:
            raise Exception("Voting is not finished yet")
        return max(self.candidates, key=self.candidates.get)

    def start_voting(self):
        self.state = State.IN_PROGRESS

    def finish_voting(self):
        self.state = State.FINISHED


class Transaction:
    def __init__(self, voter_key: str, contract_name: str, contract_method: str, args: tuple = None, timestamp: float = None,
                 signature: bytes = None):
        self.voter_key = voter_key
        self.contract_name = contract_name
        self.contract_method = contract_method
        self.args = args
        self.timestamp = time.time() if timestamp is None else timestamp
        self.signature = signature

    def to_dict(self):
        return {
            "voter_key": self.voter_key,
            "contract_name": self.contract_name,
            "contract_method": self.contract_method,
            "args": self.args,
            "timestamp": self.timestamp,
            "signature": self.signature.hex() if self.signature else None
        }

    @classmethod
    def from_dict(cls, dict_):
        obj = cls(
            voter_key=dict_['voter_key'],
            contract_name=dict_["contract_name"],
            contract_method=dict_["contract_method"],
            args=dict_["args"],
            timestamp=dict_["timestamp"],
            signature=bytes.fromhex(dict_['signature']) if dict_['signature'] else None
        )
        return obj

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return NotImplemented
        return self.voter_key == other.voter_key and \
               self.contract_name == other.contract_name and \
               self.contract_method == other.contract_method and \
               self.args == other.args and \
               self.timestamp == other.timestamp and \
               self.signature == other.signature

    def __ne__(self, other):
        if not isinstance(other, Transaction):
            return NotImplemented
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.voter_key, self.contract_name, self.contract_method, tuple(self.args) if self.args else None,
                     self.timestamp, self.signature))


# contract = SmartContract("my voting")

contracts: Dict[str,SmartContract] = {}
contract_name = "my voting"

candidate1 = "Biden"
candidate2 = "Trump"
pk1 = "Ihor"
pk2 = "Misha"

txs = []
txs.append(Transaction(pk1, contract_name, ContractMethods.CREATE))
txs.append(Transaction(pk1, contract_name, ContractMethods.START_VOTING))
txs.append(Transaction(pk1, contract_name, ContractMethods.ADD_CANDIDATE, [candidate1]))
txs.append(Transaction(pk1, contract_name, ContractMethods.ADD_CANDIDATE, [candidate2]))
txs.append(Transaction(pk1, contract_name, ContractMethods.VOTE, [pk1, candidate1]))
txs.append(Transaction(pk2, contract_name, ContractMethods.VOTE, [pk2, candidate1]))
txs.append(Transaction(pk2, contract_name, ContractMethods.FINISH_VOTING))
txs.append(Transaction(pk2, contract_name, ContractMethods.GET_RESULTS))


def execute_contract(tx):
    if tx.contract_method == ContractMethods.CREATE:
        contract = SmartContract(tx.contract_name)
        if contract in contracts:
            return False
        contracts[contract.name] = contract
        return contract
    if tx.contract_method == ContractMethods.START_VOTING:
        return contracts[tx.contract_name].start_voting()
    if tx.contract_method == ContractMethods.ADD_CANDIDATE:
        return contracts[tx.contract_name].add_candidate(*tx.args)
    if tx.contract_method == ContractMethods.VOTE:
        return contracts[tx.contract_name].vote(*tx.args)
    if tx.contract_method == ContractMethods.FINISH_VOTING:
        return contracts[tx.contract_name].finish_voting()
    if tx.contract_method == ContractMethods.GET_WINNER:
        return contracts[tx.contract_name].get_winner()
    if tx.contract_method == ContractMethods.GET_RESULTS:
        return contracts[tx.contract_name].get_results()


for tx in txs:
    result = execute_contract(tx)
    print(f"Result {result}")
    print(f"Tx {tx.to_dict()}")
