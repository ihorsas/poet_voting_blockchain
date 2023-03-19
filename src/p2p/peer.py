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
