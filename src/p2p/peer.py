class Peer:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def to_dict(self):
        return {
            "host": self.host,
            "port": self.port
        }

    @classmethod
    def from_dict(cls, dict_):
        obj = cls(
            host=dict_["host"],
            port=dict_["port"]
        )
        return obj

    def __eq__(self, other):
        if not isinstance(other, Peer):
            return NotImplemented
        return self.host == other.host and \
               self.port == other.port

    def __ne__(self, other):
        if not isinstance(other, Peer):
            return NotImplemented
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.port, self.host))