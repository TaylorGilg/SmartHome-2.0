from blockchain import Blockchain
from Interaction import Interaction
# Create a new blockchain
blockchain = Blockchain()
# Add some interactions
blockchain.new_interaction("Device1", "Device2", "Temperature: 25°C")
blockchain.new_interaction("Device2", "Device3", "Humidity: 60%")
blockchain.new_interaction("Device3", "Device1", "Pressure: 1013 hPa")
# Mine a new block
last_block = blockchain.last_block
last_proof = last_block['proof']
proof = blockchain.proof_of_work(last_proof)
blockchain.new_block(proof)
# Print the blockchain
for block in blockchain.chain:
    print("Block:", block)
    print("Interactions:")
    for interaction in block['interactions']:
        print(interaction)
    print("------------------------")