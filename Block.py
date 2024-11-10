import hashlib
import json

# Creating a basic block where we have ways to identy the block as well as proof and the previous hash for linking. It has interactions.
class Block:
    def __init__(self, index, timestamp, interactions, proof, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.interactions = interactions
        self.proof = proof
        self.previous_hash = previous_hash