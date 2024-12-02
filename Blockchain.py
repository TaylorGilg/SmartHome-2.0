import hashlib
import json
from time import time

class Blockchain:
# Blockchain class structure
    def __init__(self):
        self.chain = []
        self.current_interactions = []
        self.new_block(previous_hash=1, proof=100)

# Method to create a new block with a given proof and the previous hash on block to add it to the chain.
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
    
# Proof of Work Algorithm: First find a number p' such that hash(pp') contains leading 4 zeroes. P is previous proof.
    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof
    
# Validates the proof by checking if the hash contain 4 leading 0s
    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
    
# Determine if a given blockchain is valid by checking hash linkage and proofs  
    def is_valid_chain(self, chain=None):
        validate_chain = chain if chain is not None else self.chain
        
        for i in range(1, len(validate_chain)):
            current_block = validate_chain[i]
            previous_block = validate_chain[i - 1]
            # Check that the hash of the block is correct
            if current_block['previous_hash'] != self.hash(previous_block):
                return False
            # Check that the Proof of Work is correct
            if not self.valid_proof(previous_block['proof'], current_block['proof']):
                return False
        return True