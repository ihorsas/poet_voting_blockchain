import time

import rsa
from rsa import PublicKey, PrivateKey

from src.blockchain.contract_methods import ContractMethods


class Transaction:
    def __init__(self, voter_key: PublicKey, contract_name: str, contract_method: str, args=None,
                 timestamp: float = None,
                 signature: bytes = None):
        self.voter_key = voter_key
        self.contract_name = contract_name
        self.contract_method = contract_method
        self.args = args
        self.timestamp = time.time() if timestamp is None else timestamp
        self.signature = signature

    def sign(self, private_key: PrivateKey):
        message = f"{self.voter_key.save_pkcs1().hex()}{self.contract_name}{self.contract_method}{self.args}{self.timestamp}".encode()
        self.signature = rsa.sign(message, private_key, 'SHA-256')

    def to_dict(self):
        if self.contract_method == ContractMethods.VOTE:
            args = [self.args[0].save_pkcs1().hex(), self.args[1]]
        else:
            args = self.args

        return {
            "voter_key": self.voter_key.save_pkcs1().hex(),
            "contract_name": self.contract_name,
            "contract_method": self.contract_method,
            "args": args,
            "timestamp": self.timestamp,
            "signature": self.signature.hex() if self.signature else None
        }

    @classmethod
    def from_dict(cls, dict_):
        if dict_["contract_method"] == ContractMethods.VOTE:
            args = [rsa.PublicKey.load_pkcs1(bytes.fromhex(dict_['args'][0])), dict_["args"][1]]
        else:
            args = dict_["args"]
        obj = cls(
            voter_key=rsa.PublicKey.load_pkcs1(bytes.fromhex(dict_['voter_key'])),
            contract_name=dict_["contract_name"],
            contract_method=dict_["contract_method"],
            args=args,
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
