# Blockchain class structure - This is where we are using blocks to keep track of all device interactions in our simulated network. The blocks are put ionto a chain.
import hashlib
import json
from time import time

class Blockchain:
# Starting with an empty chain that initializes with the genesis block - the foundation or anchor for our blochain structure.
    def __init__(self):
        self.chain = []
        self.current_interactions = []
        self.new_block(previous_hash=1, proof=100) # Genesis here with initial valies!

# Creates a new block in our chain where each block contains an index, tiomestamp, interaction command, and a proof of work. We also have a hash to the previous block to reflect the chain structure. If there is no previous hash, we calculate it ourself which is crucial for the intergrity.
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
    
# Every time a device makes an interaction, it is logged with this function. We are returning the index of the block that will hold the interaction. 
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
    
# Proof of Work Algorithm: Security feature where the goal is to find a number that, when combined with the previous block's proof, creates a hash that starts with 4 zeros - similar to Bitcoin's concept but simpler.
    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof
    
# Validates the proof by checking if the hash contains 4 leading 0s
    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
    
#  Determine if a given blockchain is valid by ensuring each block points to the right previous block (chain isn't broken) amd all the proofs of work are correct. Super important for detecting if someone messed with our chain.    
    def is_valid_chain(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            # Check that the hash of the block is correct
            if current_block['previous_hash'] != self.hash(previous_block):
                return False
            # Check that the Proof of Work is correct
            if not self.valid_proof(previous_block['proof'], current_block['proof']):
                return False
        return True