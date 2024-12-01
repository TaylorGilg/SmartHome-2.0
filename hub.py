import logging
from communicator import Communicator
from socket import *
import threading
import time
import io
from PIL import Image
import traceback
from data.config import *
import json
import threading

# Configure logging
logging.basicConfig(
    filename='hub.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Serves as the main cointroller of the IoT network - where commands are sent from and keeps track of all devices. Also manages blockchain consensus protocol while keeping track of device states. 
class Hub(Communicator):

    def __init__(self, name, ip, port):
        super().__init__(name)

        # Dictionary to follow for every IoT device to keep track of them.
        self.name = name
        self._authenticated_devices = {} # Where each device is located
        self._device_locations = {}      # Where each device is located
        self._ip_to_id = {}              # Reverse lookup: get device_id from ip/port
        self._ip = ip
        self._port = int(port)
        self._buf = 1024 * 2

        self.init_sockets()
        logging.info(f"Hub '{self.name}' initialized at {ip}:{port}")
        
    def register_device(self, device_id, device_ip, device_port, location="unknown"):
        """Register a new device with the hub"""
        try:
            device_port = int(device_port)
            self._authenticated_devices[device_id] = (device_ip, device_port)
            self._ip_to_id[(device_ip, device_port)] = device_id
            self._device_locations[device_id] = location

            # Log device registration in blockchain
            self.blockchain.new_interaction(
                sender=self.name,
                recipient=device_id,
                data={
                    "type": "device_registration",
                    "ip": device_ip,
                    "port": device_port,
                    "location": location,
                    "timestamp": time.time(),
                    "status": "registered"
                }
            )
            logging.info(f"Device '{device_id}' registered at location: {location} (IP: {device_ip}, Port: {device_port})")
            print(f"Device {device_id} registered at {location}")
        except Exception as e:
            logging.error(f"Error registering device '{device_id}': {e}")
            print(f"Error registering device: {e}")
            raise

    def get_device_id(self, ip, port):
        """Get device ID from IP and port"""
        return self._ip_to_id.get((ip, int(port)), f"{ip}:{port}")

    def get_device_location(self, device_id):
        """Get device location"""
        location = self._device_locations.get(device_id, "unknown")
        logging.info(f"Retrieved location for device '{device_id}': {location}")
        return location

    def get_device_status(self):
        """Retrieve the status of all registered devices."""
        try:
            status = {
                "authenticated_devices": self._authenticated_devices,
                "device_locations": self._device_locations,
                "total_devices": len(self._authenticated_devices)
            }
            logging.info(f"Hub device status: {status}")
            return status
        except Exception as e:
            logging.error(f"Error retrieving device status: {e}")
            return {}

    def init_sockets(self):
        """Initialize TCP socket for Hub"""
        try:
            self.commSocket = socket(AF_INET, SOCK_STREAM)
            self.commSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # Allow address reuse
            self.commSocket.bind((self._ip, self._port))
            self.commSocket.listen(5)  # Listen for incoming connections
            logging.info(f"Hub '{self.name}' TCP socket initialized at {self._ip}:{self._port}")
        except Exception as e:
            logging.error(f"Error initializing sockets: {e}")
            raise

    # Allows devices to be asked for their version of the blockchain through the specified TCP port.
    # Returns a dictionary with device ID key and the device's blockchain.

    def request_blockchains(self):
        """Request blockchain data from devices via TCP"""
        blockchains = {}  # Dictionary of blockchain data with corresponding device_id as key
        for device_id, (device_ip, device_port) in self._authenticated_devices.items():
            try:
                device_tcp_port = int(device_port) + 1000
                with socket(AF_INET, SOCK_STREAM) as s:
                    s.connect((device_ip, device_tcp_port))
                    s.sendall(b"GET_BLOCKCHAIN_DATA")
                    response = s.recv(4096)
                    blockchains[device_id] = json.loads(response)
            except Exception as e:
                print(f"Error getting blockchain data from {device_id}: {e}")
        return blockchains
    
    #  Figures out which blockchain version is the "right" one.
    #   Uses these rules:
    #   1. Longest valid chain wins
    #   2. If there's a tie, the chain with more total proof-of-work wins
    #   3. If no valid chains found, use the hub's chain as fallback
    def solve_conflicts(self, blockchains):
        #holds longest valid blockchain
        longest_chain = None
        #to track length of the longest blockchain
        max_length = 0
        #sum of proofs can act as tie breaker if multiple valid chains are same max length
        best_cumulative_proof = 0

        #iterating through the blockchain dictionary
        for device_id, chain in blockchains.items():
            try:
                #validating and checking for chain of max length
                if self.blockchain.is_valid_chain(chain) and len(chain) >= max_length:
                    #calculating tie breaker
                    cumulative_proof = sum(block['proof'] for block in chain)

                    if (len(chain) > (max_length) or (len(chain) == max_length and cumulative_proof > best_cumulative_proof)):
                        #update current longest chain
                        longest_chain = chain
                        #update max length
                        max_length = len(chain)
                        #updating best current tie breaker
                        best_cumulative_proof = cumulative_proof
            except Exception as e:
                print(f"Error validating chain from {device_id}: {e}")
        #if no valid chains, default to hub's chain
        if longest_chain is None:
            return self.blockchain.chain
        else:
            return longest_chain

    # Takes the winning blockchain and tells all devices to use it while waiting for acknowledgemnt.
    def update_devices(self, resolved_chain):
        for device_id, (device_ip, device_port) in self._authenticated_devices.items():
            try:
                device_tcp_port = int(device_port) + 1000
                with socket(AF_INET, SOCK_STREAM) as s:
                    s.connect((device_ip, device_tcp_port))
                    message = f"UPDATE_BLOCKCHAIN;{json.dumps(resolved_chain)}"
                    s.sendall(message.encode("utf-8"))
                    response = s.recv(1024).decode("utf-8")
                    if response.startswith("ACK"):
                        print(f"Device {device_id} successfully updated blockchain")
                    else:
                        print(f"Device {device_id} failed to update {response}")
            except Exception as e:
                print(f"Error updating blockchain for {device_id}: {e}")

# The main consensus loop that runs forever:
# 1. Collect all blockchain versions
# 2. Pick the winner
# 3. Update everyone
# 4. Wait 60 seconds
# 5. Repeat
    def consensus_protocol(self): 
        while True:
            blockchains = self.request_blockchains()
            resolved_chain = self.solve_conflicts(blockchains)
            self.update_devices(resolved_chain)
            time.sleep(60) # run protocol periodically every 60 seconds after started 

    # Starts the consensus protocol in a separate thread so it doesn't block the rest of the hub's operations. Makes it a daemon thread so it'll stop when the program exits.
    def start_consensus_protocol(self):
        consensus_thread = threading.Thread(target=self.consensus_protocol)
        consensus_thread.daemon = True
        consensus_thread.start()
        
# First log the outgoing message in the blockchain bvefore sending. Creates a new interaction with metadata like timestamps and location.       
    def send(self, message, recipient):
        try:
            device_id = self.get_device_id(recipient[0], recipient[1])
            # Log the outgoing message
            self.blockchain.new_interaction(
                sender=self.name,
                recipient=device_id,
                data={
                    "type": "command",
                    "message": message,
                    "timestamp": time.time(),
                    "status": "sent"
                }
            )
            logging.info(f"Sending command '{message}' to device '{device_id}' at {recipient}")
            # Actually sends the message with the TCP socket and ensures it gracefully closes in the presence of errors.
            with socket(AF_INET, SOCK_STREAM) as s:
                s.connect(recipient)
                s.sendall(message.encode("utf-8"))
                logging.info(f"Message sent to device '{device_id}': {message}")
                print(f"Sent message to {device_id}: {message}")

        except Exception as e:
            logging.error(f"Error sending message to device at {recipient}: {e}")
            print(f"Error sending message: {e}")
            raise

# Receives a message from another device and logs it in the blockchain
    def receive(self):
        try:
            # Wait for the connection to be established before retriving 4096 bytes buffer.
            conn, addr = self.commSocket.accept()
            data = conn.recv(self._buf).decode("utf-8")
            plain_text = self.decrypt(data)
            # Get device ID
            device_id = self.get_device_id(addr[0], addr[1])
            # Remove text: prefix if present
            if plain_text.startswith("text:"):
                plain_text = plain_text[5:]
            # Log the incoming message
            self.blockchain.new_interaction(
                sender=device_id,
                recipient=self.name,
                data={
                    "type": "response",
                    "message": plain_text,
                    "timestamp": time.time(),
                    "status": "received"
                }
            )
            logging.info(f"Message received from device '{device_id}': {plain_text}")
            print(f"Received from {device_id}: {plain_text}")
            conn.close()
            return plain_text, addr

        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            print(f"Error receiving message: {e}")

    