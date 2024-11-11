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