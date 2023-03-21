import random
import threading

import rsa

from src.blockchain.blockchain import Blockchain
from src.p2p.p2p_server import P2PServer
from src.blockchain.transaction import Transaction

if __name__ == "__main__":
    blockchain1 = Blockchain()
    blockchain2 = blockchain1.copy()

    node1 = P2PServer('localhost', 5000, blockchain1)
    node2 = P2PServer('localhost', 5001, blockchain2)

    thread1 = threading.Thread(target=node1.start)
    thread2 = threading.Thread(target=node2.start)

    thread1.start()
    thread2.start()

    # thread1.join()
    # thread2.join()

    (public_key, private_key) = rsa.newkeys(512)
    (public_key2, private_key2) = rsa.newkeys(512)

    # Create a new transactions
    tx1 = Transaction(public_key, "Candidate A")
    blockchain1.add_transaction(tx1, private_key)
    blockchain2.add_transaction(Transaction(public_key2, "Candidate B"), private_key2)

    node1.connect_to_peer('localhost', 5001)
    # node2.connect_to_peer('localhost', 5000)

    # Wait for PoET consensus to mine a block
    blockchain2.add_transaction(Transaction(public_key2, "Candidate C"), private_key2)
    blockchain2.add_transaction(Transaction(public_key2, "Candidate D"), private_key2)
    blockchain2.add_transaction(Transaction(public_key2, "Candidate F"), private_key2)

    node1.sync()
    # node2.sync()

    print(f"Blockchain on the first node: {blockchain1.to_dict()}")
    print(f"Blockchain on the second node: {blockchain2.to_dict()}")
