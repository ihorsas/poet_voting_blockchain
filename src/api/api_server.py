import threading
import logging

import rsa
from flask import Flask, jsonify, request

from src.blockchain.blockchain import Blockchain
from src.blockchain.status import Status
from src.blockchain.transaction import Transaction
from src.blockchain.validator import Validator
from src.blockchain.smart_contract import VotingSmartContract
from src.p2p.p2p_server import P2PServer

logging.basicConfig(level=logging.DEBUG)

class ApiServer:
    def __init__(self, api_port, p2p_port):
        # Sample data structures for transactions and validators
        self.blockchain = Blockchain()
        self.public_key, self.private_key = rsa.newkeys(512)

        self.app = Flask(__name__)
        self.p2p_server = P2PServer('localhost', p2p_port, self.blockchain)

        # Register the endpoints with the app
        self.app.add_url_rule('/transactions/new', 'add_transaction', self.new_transaction, methods=['POST'])
        self.app.add_url_rule('/validators/new', 'register_validator', self.new_validator, methods=['POST'])
        self.app.add_url_rule('/transactions', 'get_transaction', self.get_transactions, methods=['GET'])
        self.app.add_url_rule('/validators', 'get_validators', self.get_validators, methods=['GET'])
        self.app.add_url_rule('/blockchain', 'get_blockchain', self.get_blockchain, methods=['GET'])
        self.app.add_url_rule('/peers', 'get_nodes', self.get_peers, methods=['GET'])
        self.app.add_url_rule('/peers/new', 'connect_to_peer', self.connect_to_peer, methods=['POST'])
        self.app.add_url_rule('/sync', 'sync_with_peers', self.sync_with_peers, methods=['GET'])
        self.app.add_url_rule('/contracts/new', 'create_contract', self.new_contract, methods=['POST'])
        self.app.add_url_rule('/contracts/candidate', 'add_candidate_to_contract', self.add_candidate_to_contract, methods=['POST'])
        self.app.add_url_rule('/contracts', 'get_contracts', self.get_contracts, methods=['GET'])

        # Define a lambda function to wrap self.app.run
        run_server = lambda port: self.app.run(port=port)

        # Create a new thread to run self.app.run in parallel
        thread1 = threading.Thread(target=run_server, args=(api_port,))
        thread2 = threading.Thread(target=self.p2p_server.start)

        thread1.start()
        thread2.start()

    def new_transaction(self):
        # Get the candidate name from the request data
        data = request.get_json()
        required_fields = ['contract', 'candidate']
        if not all(field in data for field in required_fields):
            return 'Missing fields', 400

        contract_name = request.json['contract']
        candidate_name = request.json['candidate']
        tx = Transaction(self.public_key, candidate_name, contract_name)
        # Create a new transaction and add it to the blockchain
        result, status = self.blockchain.add_transaction(tx, self.private_key)
        logging.info(f"Executed add transaction. Result: {result}, status: {status}")
        if result:
            if status == Status.NEW_BLOCK:
                self.p2p_server.broadcast_blockchain()
                return jsonify({'result': "Transaction added and new block created"}), 201
            else:
                self.p2p_server.broadcast_pending_transactions()
                return jsonify({'result': "Transaction added"}), 201

        # Return a success message
        return jsonify({"result": "Transaction were not added"}), 204

    def new_validator(self):
        # Get the validator's public key from the request data
        data = request.get_json()
        if 'address' not in data:
            return 'Missing address', 400
        public_key = request.json['address']

        # Add the validator to the set of validators
        result, wait_time = self.blockchain.register_validator(Validator(public_key))
        logging.info(f"Executed add validator. Result: {result}, wait time: {wait_time}")

        # Return the wait time as a response
        if result:
            return jsonify({"result": "Validator successfully registered", "wait_time": wait_time}), 201
        else:
            return jsonify({"result": "Validator already exist"}), 204

    def new_contract(self):
        data = request.get_json()
        if 'name' not in data:
            return 'Missing name', 400
        name = request.json['name']

        # Add the validator to the set of validators
        result = self.blockchain.deploy_contract(VotingSmartContract(name))
        logging.info(f"Executed deploy contract. Result: {result}")

        # Return the wait time as a response
        if result:
            self.p2p_server.broadcast_contracts()
            return jsonify({"result": "Contract successfully deployed"}), 201
        else:
            return jsonify({"result": "Contract already exist"}), 204

    def add_candidate_to_contract(self):
        data = request.get_json()
        required_fields = ['contract', 'candidate']
        if not all(field in data for field in required_fields):
            return 'Missing fields', 400

        contract = request.json['contract']
        candidate = request.json['candidate']

        # Add the validator to the set of validators
        result = self.blockchain.add_candidate_to_contract(contract, candidate)
        logging.info(f"Executed add candidate to contract. Result: {result}")

        # Return the wait time as a response
        if result:
            self.p2p_server.broadcast_candidates()
            return jsonify({"result": "Candidate successfully added to contract"}), 201
        else:
            return jsonify({"result": "Candidate already exists in contract"}), 204

    def connect_to_peer(self):
        # Get the validator's public key from the request data
        data = request.get_json()
        required_fields = ['host', 'port']
        if not all(field in data for field in required_fields):
            return 'Missing fields', 400

        host = request.json['host']
        port = request.json['port']

        result = self.p2p_server.connect_to_peer(host, port)
        logging.info(f"Executed connect to peer. Result: {result}")

        if result:
            return jsonify({"result": "Peer successfully connected"}), 201
        else:
            return jsonify({"result": "Peer already exist"}), 204

    def sync_with_peers(self):
        result = self.p2p_server.sync()
        logging.info(f"Executed connect to peer. Result: {result}")

        if result:
            return jsonify({"result": "Peer successfully connected"}), 201
        else:
            return jsonify({"result": "Peer already exist"}), 204

    def get_transactions(self):
        txs = [tx.to_dict() for tx in self.blockchain.pending_transactions]
        return txs, 200

    def get_validators(self):
        validators = [tx.to_dict() for tx in self.blockchain.validators]
        return validators, 200

    def get_blockchain(self):
        return Blockchain.to_dict(self.blockchain), 200

    def get_peers(self):
        peers = [peer.to_dict() for peer in self.p2p_server.p2p_node.peers]
        return peers, 200

    def get_contracts(self):
        contracts = [contract for contract in self.blockchain.contracts]
        return contracts, 200

