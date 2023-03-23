import json

import rsa


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

    def is_candidate_exist(self, candidate):
        return candidate in self.candidates

    def is_voter_key_exist(self, voter_key):
        return voter_key in self.votes

    def vote(self, voter_key, candidate):
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

    def get_winner(self):
        if self.state != State.FINISHED:
            raise Exception("Voting is not finished yet")
        return max(self.candidates, key=self.candidates.get)

    def start_voting(self):
        self.state = State.IN_PROGRESS

    def finish_voting(self):
        self.state = State.FINISHED

    def to_dict(self):
        return {
            "name": self.name,
            "votes": {voter_key: self.votes[voter_key].save_pkcs1().hex() for voter_key in self.votes},
            "candidates": self.candidates,
            "state": self.state
        }

    @classmethod
    def from_dict(cls, dict_):
        obj = cls(dict_['name'])
        obj.state = dict_['state']
        obj.votes = {voter_key: rsa.PublicKey.load_pkcs1(bytes.fromhex(dict_['votes'][voter_key])) for voter_key in
                     dict_['votes']}
        obj.candidates = dict_['candidates']
        return obj

    def __eq__(self, other):
        if not isinstance(other, VotingSmartContract):
            return NotImplemented

        return self.name == other.name and self.votes == other.votes and \
               self.state == other.state and self.candidates == other.candidates

    def __ne__(self, other):
        if not isinstance(other, VotingSmartContract):
            return NotImplemented
        return not self.__eq__(other)

    def __hash__(self):
        return hash((json.dumps(self.votes),json.dumps(self.candidates), self.name, self.state))
