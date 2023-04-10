import time


class State:
    NOT_STARTED = "not_started"
    FINISHED = "finished"
    IN_PROGRESS = "in_progress"


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
    def __init__(self, voter_key: str, contract, args=None, timestamp: float = None,
                 signature: bytes = None):
        self.voter_key = voter_key
        self.contract = contract
        self.args = args
        self.timestamp = time.time() if timestamp is None else timestamp
        self.signature = signature

    def execute_contract(self):
        if self.args is not None:
            return self.contract(*self.args)
        else:
            return self.contract()

    def to_dict(self):
        return {
            "voter_key": self.voter_key,
            "contract": self.contract,
            "args": self.args,
            "timestamp": self.timestamp,
            "signature": self.signature.hex() if self.signature else None
        }

    @classmethod
    def from_dict(cls, dict_):
        obj = cls(
            voter_key=dict_['voter_key'],
            contract=dict_["contract"],
            args=dict_["args"],
            timestamp=dict_["timestamp"],
            signature=bytes.fromhex(dict_['signature']) if dict_['signature'] else None
        )
        return obj

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return NotImplemented
        return self.voter_key == other.voter_key and \
               self.contract == other.contract and \
               self.args == other.args and \
               self.timestamp == other.timestamp and \
               self.signature == other.signature

    def __ne__(self, other):
        if not isinstance(other, Transaction):
            return NotImplemented
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.voter_key, self.contract, tuple(self.args) if self.args else None, self.timestamp, self.signature))


contract = SmartContract("my voting")

candidate1 = "Biden"
candidate2 = "Trump"
pk1 = "Ihor"
pk2 = "Misha"

txs = []
txs.append(Transaction(pk1, contract.__init__, ["my voting"]))
txs.append(Transaction(pk1, contract.start_voting))
txs.append(Transaction(pk1, contract.add_candidate, [candidate1]))
txs.append(Transaction(pk1, contract.add_candidate, [candidate2]))
txs.append(Transaction(pk1, contract.vote, [pk1, candidate1]))
txs.append(Transaction(pk2, contract.vote, [pk2, candidate1]))
txs.append(Transaction(pk2, contract.finish_voting))
txs.append(Transaction(pk2, contract.get_results))

for tx in txs:
    result = tx.execute_contract()
    print(f"Result {result}")
    print(f"Tx {tx.to_dict()}")
