import time

import rsa


class Transaction:
    def __init__(self, voter_key, candidate, timestamp=None, signature=None):
        self.voter_key = voter_key
        self.candidate = candidate
        self.timestamp = time.time() if timestamp is None else timestamp
        self.signature = signature

    def sign(self, private_key):
        message = f"{self.voter_key}{self.candidate}{self.timestamp}".encode()
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
