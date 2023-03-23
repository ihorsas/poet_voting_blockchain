import hashlib
import random
import threading
import time

# do not care
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


class State:
    NOT_STARTED = "not_started"
    FINISHED = "finished"
    IN_PROGRESS = "in_progress"


class VotingSmartContract:
    def __init__(self, unique_name):
        self.name = unique_name
        self.votes = {}
        self.candidates = {}
        self.state = State.NOT_STARTED

    def add_candidate(self, candidate):
        if candidate in self.candidates:
            raise Exception(f"{candidate} already exists.")
        self.candidates[candidate] = 0

    def vote(self, voter_key, candidate):
        if candidate not in self.candidates:
            raise Exception(f"{candidate} does not exist.")
        if voter_key in self.votes:
            raise Exception(f"Voter {voter_key} already voted.")
        # Check if the voting period has started
        if self.state == State.NOT_STARTED:
            raise Exception("Error: Voting period has not started yet.")
        # Check if the voting period has ended
        if self.state == State.FINISHED:
            raise Exception("Error: Voting period has ended.")
        self.votes[voter_key] = candidate
        self.candidates[candidate] += 1

    def get_results(self):
        if self.state != State.FINISHED:
            raise Exception("Voting is not finished yet")
        return self.candidates

    def get_winner(self):
        if self.state != State.FINISHED:
            raise Exception("Voting is not finished yet")
        return max(self.candidates, key=self.candidates.get)

    def start_voting(self):
        self.state = State.IN_PROGRESS

    def finish_voting(self):
        self.state = State.FINISHED

class Transaction:
    def __init__(self, voter_key, candidate, contract):
        self.voter_key = voter_key
        self.candidate = candidate
        self.contract = contract
        self.timestamp = time.time()
        self.signature = None

    def sign(self, private_key):
        message = hashlib.sha256(str(self).encode()).digest()
        self.signature = private_key.sign(message)

class Blockchain:
    def __init__(self):
        self.chain = [Block(1, [], 0, "0")]
        self.current_transactions = []
        self.contracts = {}

    def deploy_contract(self, contract: VotingSmartContract):
        self.contracts[contract.name] = contract

    def add_candidate_to_contract(self, contract_name, candidate):
        self.contracts.get(contract_name).add_candidate(candidate)

    def add_block(self, block):
        self.chain.append(block)
        return True

    def add_transaction(self, transaction):
        self.current_transactions.append(transaction)
        if len(self.current_transactions) == 5:
            block = Block(len(self.chain), self.current_transactions, time.time(), self.chain[-1].hash)
            self.add_block(block)
            for tx in self.current_transactions:
                current_contract = self.get_contract_by_name(tx.contract)
                if current_contract is not None:
                    current_contract.vote(tx.voter_key, tx.candidate)
            self.current_transactions = []
            return True
        return False

    def get_contract_by_name(self, contract_name):
        return self.contracts.get(contract_name)

    def start_voting(self, contract_name):
        self.contracts.get(contract_name).start_voting()

    def finish_voting(self, contract_name):
        self.contracts.get(contract_name).finish_voting()

    def get_results(self, contract_name):
        return self.contracts.get(contract_name).get_results()

    def get_winner(self, contract_name):
        return self.contracts.get(contract_name).get_winner()

class Block:
    def __init__(self, index, transactions, timestamp, previous_hash, smart_contract_results=None):
        self.index = index
        self.transactions = transactions
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()
        self.smart_contract_results = smart_contract_results if smart_contract_results is not None else {}

    def execute_smart_contract(self, smart_contract):
        # execute the smart contract
        results = smart_contract.execute()

        # store the results in the block's smart_contract_results dictionary
        self.smart_contract_results[smart_contract.identifier] = results

    def compute_hash(self):
        return hashlib.sha256(str(self.index).encode() +
                              str(self.transactions).encode() +
                              str(self.timestamp).encode() +
                              str(self.previous_hash).encode()).hexdigest()



# Create smart contract
contract = VotingSmartContract("Voting Contract")

# Create blockchain and register validators
blockchain = Blockchain()

# Add smart contract to blockchain
blockchain.deploy_contract(contract)

# Add candidates to the smart contract
contract.add_candidate("Alice")
contract.add_candidate("Bob")
contract.add_candidate("Charlie")

# Create transactions to cast votes
tx1 = Transaction("Voter1", "Alice", contract.name)
tx2 = Transaction("Voter2", "Bob", contract.name)
tx3 = Transaction("Voter3", "Charlie", contract.name)
tx4 = Transaction("Voter4", "Charlie", contract.name)
tx5 = Transaction("Voter5", "Charlie", contract.name)

blockchain.start_voting(contract.name)

# Add transactions to blockchain
blockchain.add_transaction(tx1)
blockchain.add_transaction(tx2)
blockchain.add_transaction(tx3)
blockchain.add_transaction(tx4)
blockchain.add_transaction(tx5)

blockchain.finish_voting(contract.name)

print(len(blockchain.contracts))
# Get results from smart contract
results = blockchain.get_results(contract.name)

# Print results
for candidate, votes in results.items():
    print(f"{candidate}: {votes}")

winner = blockchain.get_winner(contract.name)

print(f"Winner: {winner}")