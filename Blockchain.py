import hashlib
import json
from time import time

class Blockchain:
# Blockchain class structure
    def __init__(self):
        self.chain = []
        self.current_interactions = []
        self.new_block(previous_hash=1, proof=100)

# Method to create a new blocjk with a given proof and the previous hash on block to add it to the chain.
    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'interactions': self.current_interactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_interactions = []
        self.chain.append(block)
        return block
    
# Adds a new interaction to a list of current interactions and returns the index of the block that holds the interaction.  
    def new_interaction(self, sender, recipient, data):
        self.current_interactions.append({
            'sender': sender,
            'recipient': recipient,
            'data': data,
        })
        return self.last_block['index'] + 1

# Returns the last block of chain.
    @property
    def last_block(self):
        return self.chain[-1]
    
# Hashing method for blockhain class that takes a block and returns its SHA-256 hash by first converting to a JSON.
    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()