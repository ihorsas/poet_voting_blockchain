import json
import logging
import socket
import threading

from rsa import PublicKey

from src.blockchain.block import Block
from src.blockchain.blockchain import Blockchain
from src.blockchain.smart_contract import VotingSmartContract
from src.blockchain.transaction import Transaction
from src.p2p.message import MessageTypes
from src.p2p.node import Node
from src.p2p.peer import Peer
from src.p2p.validator import Validator

logging.basicConfig(level=logging.DEBUG)

HEADER_SIZE = 10


class P2PServer:
    def __init__(self, host: int, port: int, blockchain: Blockchain):
        self.host = host
        self.port = port
        self.p2p_node = Node(blockchain, list(), list())
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        logging.info(f"Listening on {self.host}:{self.port}")

    def start(self):
        logging.info("Starting node...")
        self.broadcast_myself()  # Send peer info to other nodes upon starting up
        while True:
            try:
                conn, addr = self.server_socket.accept()
                logging.info(f"Accepted connection from {addr}")
                threading.Thread(target=self.handle_connection, args=(conn,)).start()
            except Exception as e:
                logging.exception(e)

    def receive_all(self, conn, length):
        data = b''
        while len(data) < length:
            packet = conn.recv(length - len(data))
            if not packet:
                return None
            data += packet
        return data

    def receive_message(self, conn):
        # Receive message header
        header = self.receive_all(conn, HEADER_SIZE)
        if not header:
            return None
        # Extract message length from header
        msg_len = int(header.decode())
        # Receive message body
        body = self.receive_all(conn, msg_len)
        if not body:
            return None
        # Decode message body from bytes to JSON
        message = json.loads(body.decode())
        return message

    def handle_connection(self, conn):
        with conn:
            message = self.receive_message(conn)
            host, port = conn.getpeername()
            curr_peer = Peer(host, port)
            logging.info(f"Received {message} from {curr_peer.to_dict()}")

            if message['type'] == MessageTypes.NEW_TRANSACTION:
                transaction = Transaction.from_dict(message['transaction'])
                if self.p2p_node.add_transaction(transaction):
                    logging.info(f"Sending transaction {message}")
                    self.broadcast(message)
            elif message['type'] == MessageTypes.NEW_BLOCK:
                block = Block.from_dict(message['block'])
                if self.p2p_node.add_block(block):
                    logging.info(f"Sending block {message}")
                    self.broadcast(message)
            elif message['type'] == MessageTypes.NEW_PEER:
                peer = Peer.from_dict(message['peer'])
                if peer not in self.p2p_node.peers:
                    self.p2p_node.add_peer(peer)
                # self.broadcast_peers()
                # self.sync()
            elif message['type'] == MessageTypes.NEW_VALIDATOR:
                validator = Validator.from_dict(message['validator'])
                if self.p2p_node.add_validator(validator):
                    logging.info(f"Sending validator {validator}")
                    self.broadcast(message)
            elif message['type'] == MessageTypes.GET_BLOCKCHAIN:
                # pass
                peer = Peer.from_dict(message['address'])
                self.send_blockchain(peer)
            elif message['type'] == MessageTypes.GET_PENDING_TRANSACTIONS:
                # pass
                peer = Peer.from_dict(message['address'])
                self.send_pending_transactions(peer)
            elif message['type'] == MessageTypes.PENDING_TRANSACTIONS:
                for tx_dict in message['transactions']:
                    tx = Transaction.from_dict(tx_dict)
                    self.p2p_node.add_transaction(tx)
            elif message['type'] == MessageTypes.BLOCKCHAIN:
                blockchain = Blockchain.from_dict(message['blockchain'])
                if self.p2p_node.sync_blockchain(blockchain):
                    self.broadcast_blockchain()
            elif message['type'] == MessageTypes.SYNC:
                pass
                # self.sync_with_peer(curr_peer)
            elif message['type'] == MessageTypes.VALIDATE_NEW_BLOCK:
                block = Block.from_dict(message['block'])
                if self.p2p_node.validate_block(block):
                    logging.info(f"Sending block {message}")
                    self.send_block(block)
            elif message['type'] == MessageTypes.GENERATE_WAIT_TIME:
                wait_time = self.p2p_node.generate_wait_time_for_local_validator()
                address = self.p2p_node.local_validator.address
                peer = Peer.from_dict(message['address'])
                self.send_wait_time(peer, wait_time, address)
            elif message['type'] == MessageTypes.WAIT_TIME:
                wait_time = message['wait_time']
                address = Peer.from_dict(message['address'])
                self.p2p_node.add_wait_time_for_validator(wait_time, address)
            elif message['type'] == MessageTypes.ADD_ELAPSED_TIME:
                time = message['time']
                self.p2p_node.increase_wait_time_for_validator(time)
            else:
                logging.warning(f"Invalid message type: {message['type']}")

    def broadcast(self, message):
        logging.info(f"Broadcasting {message}")
        for peer in self.p2p_node.peers:
            self.send_message(peer, message)

    def send_message(self, peer, message):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(30)
                # Set the socket option SO_KEEPALIVE to 1 (enabled)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)

                # Get the current value of SO_KEEPALIVE option
                keepalive = s.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE)

                # wait untill socket keeps alive
                while not keepalive:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                    keepalive = s.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE)

                s.connect((peer.host, peer.port))

                # Convert message to bytes
                message_bytes = json.dumps(message).encode()

                # Create header
                header = f"{len(message_bytes):<10}".encode()

                # Send header and message together
                s.sendall(header + message_bytes)

            except ConnectionRefusedError:
                logging.warning(f"Connection to {peer} refused")

    def broadcast_peers(self):
        for peer in self.p2p_node.peers:
            message = {'type': MessageTypes.NEW_PEER, 'peer': peer.to_dict()}
            self.broadcast(message)

    def broadcast_myself(self):
        message = {'type': MessageTypes.NEW_PEER, 'peer': Peer(self.host, self.port).to_dict()}
        self.broadcast(message)

    def send_blockchain(self, peer):
        message = {'type': MessageTypes.BLOCKCHAIN, 'blockchain': self.p2p_node.blockchain.to_dict()}
        self.send_message(peer, message)

    def broadcast_blockchain(self):
        message = {'type': MessageTypes.BLOCKCHAIN, 'blockchain': self.p2p_node.blockchain.to_dict()}
        self.broadcast(message)

    def send_pending_transactions(self, peer):
        message = {'type': MessageTypes.PENDING_TRANSACTIONS,
                   'transactions': [tx.to_dict() for tx in self.p2p_node.blockchain.pending_transactions]}
        self.send_message(peer, message)

    def broadcast_pending_transactions(self):
        message = {'type': MessageTypes.PENDING_TRANSACTIONS,
                   'transactions': [tx.to_dict() for tx in self.p2p_node.blockchain.pending_transactions]}
        self.broadcast(message)

    def broadcast_contracts(self):
        contracts = self.p2p_node.blockchain.contracts
        message = {'type': MessageTypes.CONTRACTS,
                   'contracts': {name: contracts[name].to_dict() for name in contracts}}
        self.broadcast(message)

    def send_block(self, block):
        message = {'type': MessageTypes.NEW_BLOCK,
                   'block': Block.to_dict(block)}
        self.broadcast(message)

    def send_contract(self, contract):
        message = {'type': MessageTypes.NEW_CONTRACT,
                   'contract': VotingSmartContract.to_dict(contract)}
        self.broadcast(message)

    def sync(self):
        logging.info(f"Syncing node with peers {[peer.to_dict() for peer in self.p2p_node.peers]}")
        for peer in self.p2p_node.peers:
            self.send_message(peer,
                              {'type': MessageTypes.GET_BLOCKCHAIN, 'address': Peer(self.host, self.port).to_dict()})

    def connect_to_peer(self, host, port):
        peer = Peer(host, port)
        if peer not in self.p2p_node.peers:
            self.p2p_node.peers.append(peer)
            self.send_message(peer, {'type': MessageTypes.NEW_PEER, 'peer': Peer(self.host, self.port).to_dict()})
            self.sync()
            return True
        return False

    def sync_with_peer(self, peer):
        self.send_blockchain(peer)
        self.send_pending_transactions(peer)
        self.broadcast_peers()

    def register_validator(self, public_key: PublicKey):
        validator = Validator(public_key, Peer(self.host, self.port))
        if self.p2p_node.register_validator(validator):
            message = {
                'type': MessageTypes.NEW_VALIDATOR,
                'validator': validator.to_dict(),
            }
            self.broadcast(message)
            return True
        return False

    def start_validating(self):
        min_elapsed_time = self.init_new_round()
        while not self.p2p_node.are_all_validators_have_wait_time(min_elapsed_time):
            pass

        block_to_add = self.p2p_node.blockchain.get_new_block()
        message = {
            'type': MessageTypes.VALIDATE_NEW_BLOCK,
            'block': block_to_add.to_dict(),
        }
        for v in self.p2p_node.validators:
            self.send_message(v.address, message)

    def init_new_round(self):
        self.generate_wait_times()
        return self.add_elapsed_time()

    def generate_wait_times(self):
        message = {
            'type': MessageTypes.GENERATE_WAIT_TIME,
            'address': Peer(self.host, self.port).to_dict()
        }
        for v in self.p2p_node.validators:
            self.send_message(v.address, message)

    def send_wait_time(self, peer, wait_time, address: Peer):
        message = {
            'type': MessageTypes.WAIT_TIME,
            'wait_time': wait_time,
            'address': address.to_dict()
        }
        self.send_message(peer, message)

    def add_elapsed_time(self):
        while not self.p2p_node.are_all_validators_have_wait_time():
            pass

        elapsed_times = [v.wait_time for v in self.p2p_node.validators]
        min_elapsed_time = min(elapsed_times)
        message = {
            'type': MessageTypes.ADD_ELAPSED_TIME,
            'time': min_elapsed_time
        }
        for v in self.p2p_node.validators:
            self.send_message(v.address, message)
        return min_elapsed_time
