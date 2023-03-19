import json
import time

import rsa


class Transaction:
    def __init__(self, voter_key, candidate, timestamp=None, signature=None):
        self.voter_key = voter_key
        self.candidate = candidate
        self.timestamp = time.time() if timestamp is None else timestamp
        self.signature = signature

    def sign(self, private_key):
        message = f"{self.voter_key.save_pkcs1().hex()}{self.candidate}{self.timestamp}".encode()
        self.signature = rsa.sign(message, private_key, 'SHA-256')

    def to_dict(self):
        return {
            "voter_key": self.voter_key.save_pkcs1().hex(),
            "candidate": self.candidate,
            "timestamp": self.timestamp,
            "signature": self.signature.hex() if self.signature else None
        }

    @classmethod
    def from_dict(cls, dict_):
        obj = cls(
            voter_key=rsa.PublicKey.load_pkcs1(bytes.fromhex(dict_['voter_key'])),
            candidate=dict_["candidate"],
            timestamp=dict_["timestamp"],
            signature=bytes.fromhex(dict_['signature']) if dict_['signature'] else None
        )
        return obj

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return NotImplemented
        return self.voter_key == other.voter_key and \
               self.candidate == other.candidate and \
               self.timestamp == other.timestamp and \
               self.signature == other.signature

    def __ne__(self, other):
        if not isinstance(other, Transaction):
            return NotImplemented
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.voter_key, self.candidate, self.timestamp, self.signature))

    # def __hash__(self):
    #     str_dict = json.dumps(self.to_dict(), sort_keys=True)
    #     hash_of_dict = hash(str_dict)
    #     # print(f"asking for hash. Here it is for {self.to_dict()}: {hash_of_dict}")
    #     return hash_of_dict
    #
    # def __eq__(self, other):
    #     return self.__hash__ == other.__hash__
    #
    # def __ne__(self, other):
    #     return self.__hash__ != other.__hash__
    #
