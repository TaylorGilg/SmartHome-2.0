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
# Similar to the interaction class where we convert the block into a format for Blockchain usage
    def to_dict(self):
        return {
         'index': self.index,
         'timestamp': self.timestamp,
         'interactions': [interaction.to_dict() for interaction in self.interactions],
         'proof': self.proof,
         'previous_hash': self.previous_hash,
      }