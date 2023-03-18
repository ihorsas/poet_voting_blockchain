import json
import rsa

# Generate a public/private key pair for the voter
from src.block import Block
from src.blockchain import Blockchain
from src.transaction import Transaction

(public_key, private_key) = rsa.newkeys(512)

# TODO: example of transaction serialization/deserialization
# # Create a Transaction instance
# tx = Transaction(public_key, "you")
#
# # Sign the transaction
# tx.sign(private_key)
#
# # Serialize the Transaction object to a dictionary
# tx_dict = tx.to_dict()
#
# # Convert the dictionary to a JSON string
# tx_json = json.dumps(tx_dict)
#
# # Deserialize the JSON string to a dictionary
# tx_dict2 = json.loads(tx_json)
#
# # Convert the dictionary back to a Transaction object
# tx2 = Transaction.from_dict(tx_dict2)

# TODO: example of block serialization/deserialization
# # create a block object
# tx1 = Transaction(public_key, 'Alice')
# tx1.sign(private_key)
# block = Block(transactions=[tx1], previous_hash='abc', wait_time=60)
#
# # serialize the block object to JSON
# block_json = json.dumps(block.to_dict(), indent=4)
#
# # deserialize the block JSON to a block object
# block_obj = Block.from_dict(json.loads(block_json))
#

# TODO: example of blockchain serialization/deserialization
# # create a Blockchain object and add some transactions
# blockchain = Blockchain()
# tx1 = Transaction(public_key, "Alice")
# tx2 = Transaction(public_key, "Bob")
# blockchain.add_transaction(tx1, private_key)
# blockchain.add_transaction(tx2, private_key)
#
# # serialize the blockchain to a JSON string
# blockchain_json = json.dumps(blockchain.to_dict(), indent=4)
#
# # deserialize the JSON string back into a Blockchain object
# blockchain_dict = json.loads(blockchain_json)
# blockchain_deserialized = Blockchain.from_dict(blockchain_dict)
#
# # print the deserialized blockchain to confirm it matches the original
# print(blockchain_deserialized.chain)

# Create a blockchain
blockchain = Blockchain()

# Create a new transactions
blockchain.add_transaction(Transaction(public_key, "Candidate A"), private_key)
blockchain.add_transaction(Transaction(public_key, "Candidate B"), private_key)

# Wait for PoET consensus to mine a block
new_block = blockchain.mine_block()

print("New block added to the chain:")
print(json.dumps(new_block.to_dict(), indent=4))
new_block = json.loads(json.dumps(new_block.to_dict(), indent=4))
