import logging
import threading

import rsa
from flask import Flask, jsonify, request

from src.blockchain.blockchain import Blockchain
from src.blockchain.contract_methods import ContractMethods
from src.blockchain.status import Status
from src.blockchain.transaction import Transaction
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
        self.app.add_url_rule('/votes/new', 'add_transaction', self.new_vote, methods=['POST'])
        self.app.add_url_rule('/validators/register', 'register_validator', self.register_validator, methods=['POST'])
        self.app.add_url_rule('/transactions', 'get_transaction', self.get_transactions, methods=['GET'])
        self.app.add_url_rule('/validators', 'get_validators', self.get_validators, methods=['GET'])
        self.app.add_url_rule('/blockchain', 'get_blockchain', self.get_blockchain, methods=['GET'])
        self.app.add_url_rule('/peers', 'get_nodes', self.get_peers, methods=['GET'])
        self.app.add_url_rule('/peers/new', 'connect_to_peer', self.connect_to_peer, methods=['POST'])
        self.app.add_url_rule('/sync', 'sync_with_peers', self.sync_with_peers, methods=['GET'])
        self.app.add_url_rule('/contracts/new', 'create_contract', self.new_contract, methods=['POST'])
        self.app.add_url_rule('/contract/candidate', 'add_candidate_to_contract', self.add_candidate_to_contract,
                              methods=['PUT'])
        self.app.add_url_rule('/contract/start', 'start_contract', self.start_contract, methods=['PUT'])
        self.app.add_url_rule('/contract/finish', 'finish_contract', self.finish_contract, methods=['PUT'])
        self.app.add_url_rule('/contracts', 'get_contracts', self.get_contracts, methods=['GET'])
        self.app.add_url_rule('/contract/results', 'get_results', self.get_results, methods=['GET'])

        # Define a lambda function to wrap self.app.run
        run_server = lambda port: self.app.run(port=port)

        # Create a new thread to run self.app.run in parallel
        thread1 = threading.Thread(target=run_server, args=(api_port,))
        thread2 = threading.Thread(target=self.p2p_server.start)

        thread1.start()
        thread2.start()

    def new_vote(self):
        # Get the candidate name from the request data
        data = request.get_json()
        required_fields = ['contract', 'candidate']
        if not all(field in data for field in required_fields):
            return 'Missing fields', 400

        contract_name = request.json['contract']
        candidate_name = request.json['candidate']
        tx = Transaction(self.public_key, contract_name, ContractMethods.VOTE, [self.public_key, candidate_name])
        # Create a new transaction and add it to the blockchain
        result, status = self.blockchain.add_transaction(tx, self.private_key)
        logging.info(f"Executed vote. Result: {result}, status: {status}")
        if result:
            if status == Status.NEW_BLOCK:
                self.p2p_server.start_validating()
                return jsonify({'result': "Vote added and new block created"}), 201
            else:
                self.p2p_server.broadcast_pending_transactions()
                return jsonify({'result': "Vote added"}), 201
        return jsonify({'result': "Smth went wrong"}), 400

    def register_validator(self):
        # Add the validator to the set of validators
        result = self.p2p_server.register_validator(self.public_key)
        logging.info(f"Executed add validator. Result: {result}")

        # Return the wait time as a response
        if result:
            return jsonify({"result": "Validator successfully registered"}), 201
        else:
            return jsonify({"result": "Validator already exist"}), 204

    def new_contract(self):
        data = request.get_json()
        if 'name' not in data:
            return 'Missing name', 400
        name = request.json['name']

        tx = Transaction(self.public_key, name, ContractMethods.CREATE)

        result, status = self.blockchain.add_transaction(tx, self.private_key)
        logging.info(f"Executed add contract. Result: {result}, status: {status}")
        if result:
            if status == Status.NEW_BLOCK:
                self.p2p_server.start_validating()
                return jsonify({'result': "Contract added and new block created"}), 201
            else:
                self.p2p_server.broadcast_pending_transactions()
                return jsonify({'result': "Contract added"}), 201
        return jsonify({'result': "Smth went wrong"}), 400

    def add_candidate_to_contract(self):
        data = request.get_json()
        required_fields = ['contract', 'candidate']
        if not all(field in data for field in required_fields):
            return 'Missing fields', 400

        contract = request.json['contract']
        candidate = request.json['candidate']

        tx = Transaction(self.public_key, contract, ContractMethods.ADD_CANDIDATE, [candidate])

        result, status = self.blockchain.add_transaction(tx, self.private_key)
        logging.info(f"Executed add candidate to contract. Result: {result}, status: {status}")
        if result:
            if status == Status.NEW_BLOCK:
                self.p2p_server.start_validating()
                return jsonify({'result': "Candidate added to contract and new block created"}), 201
            else:
                self.p2p_server.broadcast_pending_transactions()
                return jsonify({'result': "Candidate added to contract"}), 201
        return jsonify({'result': "Smth went wrong"}), 400

    def start_contract(self):
        data = request.get_json()
        required_fields = ['contract']
        if not all(field in data for field in required_fields):
            return 'Missing fields', 400

        contract = request.json['contract']

        tx = Transaction(self.public_key, contract, ContractMethods.START_VOTING)

        result, status = self.blockchain.add_transaction(tx, self.private_key)
        logging.info(f"Executed start voting. Result: {result}, status: {status}")
        if result:
            if status == Status.NEW_BLOCK:
                self.p2p_server.start_validating()
                return jsonify({"result": "Executed start voting successfully and new block created"}), 201
            else:
                self.p2p_server.broadcast_pending_transactions()
                return jsonify({'result': "Executed start voting"}), 201
        return jsonify({'result': "Smth went wrong"}), 400

    def finish_contract(self):
        data = request.get_json()
        required_fields = ['contract']
        if not all(field in data for field in required_fields):
            return 'Missing fields', 400

        contract = request.json['contract']

        tx = Transaction(self.public_key, contract, ContractMethods.FINISH_VOTING)

        result, status = self.blockchain.add_transaction(tx, self.private_key)
        logging.info(f"Executed finish voting. Result: {result}, status: {status}")
        if result:
            if status == Status.NEW_BLOCK:
                self.p2p_server.start_validating()
                return jsonify({"result": "Executed finish voting successfully and new block created"}), 201
            else:
                self.p2p_server.broadcast_pending_transactions()
                return jsonify({'result': "Executed finish voting"}), 201
        return jsonify({'result': "Smth went wrong"}), 400

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
        validators = self.p2p_server.p2p_node.validators
        validators = [v.to_dict() for v in validators]
        return validators, 200

    def get_blockchain(self):
        return Blockchain.to_dict(self.blockchain), 200

    def get_peers(self):
        peers = [peer.to_dict() for peer in self.p2p_server.p2p_node.peers]
        return peers, 200

    def get_contracts(self):
        contracts = [contract for contract in self.blockchain.contracts]
        return contracts, 200

    def get_results(self):
        data = request.get_json()
        required_fields = ['contract']
        if not all(field in data for field in required_fields):
            return 'Missing fields', 400

        contract = request.json['contract']
        results = self.blockchain.get_results(contract)
        return results, 200
