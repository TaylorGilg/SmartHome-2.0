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
import socket
import hmac
import hashlib

# Configure logging
logging.basicConfig(
    filename='hub.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

class Hub(Communicator):

    def __init__(self, name, ip, port):
        super().__init__(name)

        # assign private properties
        self.name = name
        self._authenticated_devices = {}  # {device_id: (ip, port)}
        self._device_locations = {}      # {device_id: location}
        self._ip_to_id = {}              # {(ip, port): device_id}
        self._ip = ip
        self._port = int(port)
        self._buf = 1024 * 2
        self.mac_key = b"super_secret_key" # Shared key for HMAC

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

    def get_blockchain_data(self, device_id):
        try:
            device_ip, device_port = self._authenticated_devices[device_id]
            device_tcp_port = int(device_port) + 1000 #TCP port 1000 more

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(5) #timeout after 5 seconds
                s.connect((device_ip, device_tcp_port))
                s.sendall(b"GET_BLOCKCHAIN_DATA")
                response = s.recv(4096)
                return json.loads(response)
            
        except (socket.timeout, ConnectionRefusedError) as e:
            print(f"Connection to device {device_id} falied: {e}")
            return []
        except Exception as e:
            print(f"Error getting blockchain data from device {device_id}: {e}")
            return []

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
            self.commSocket = socket.socket(AF_INET, SOCK_STREAM)
            self.commSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)  # Allow address reuse
            self.commSocket.bind((self._ip, self._port))
            self.commSocket.listen(5)  # Listen for incoming connections
            logging.info(f"Hub '{self.name}' TCP socket initialized at {self._ip}:{self._port}")
        except Exception as e:
            logging.error(f"Error initializing sockets: {e}")
            raise

    #Consensus Protocol Methods: 

    def request_blockchains(self):
        """Request blockchain data from devices via TCP"""
        blockchains = {}  # Dictionary of blockchain data with corresponding device_id as key
        for device_id, (device_ip, device_port) in self._authenticated_devices.items():
            try:
                device_tcp_port = int(device_port) + 1000
                with socket.socket(AF_INET, SOCK_STREAM) as s:
                    s.connect((device_ip, device_tcp_port))
                    s.sendall(b"GET_BLOCKCHAIN_DATA")
                    response = s.recv(4096)
                    blockchains[device_id] = json.loads(response)
            except Exception as e:
                print(f"Error getting blockchain data from {device_id}: {e}")
        return blockchains
    
    #solves conflicts between varying ledgers between devices
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

    #takes in resolved chain and sends it out to devices via TCP connection
    def update_devices(self, resolved_chain):
        """Send resolved blockchain data to devices via TCP"""
        for device_id, (device_ip, device_port) in self._authenticated_devices.items():
            try:
                device_tcp_port = int(device_port) + 1000
                with socket.socket(AF_INET, SOCK_STREAM) as s:
                    s.connect((device_ip, device_tcp_port))
                    message = f"UPDATE_BLOCKCHAIN;{json.dumps(resolved_chain)}"
                    s.sendall(message.encode("utf-8"))
                    response = s.recv(1024).decode("utf-8")
                    if response.startswith("ACK"):
                        print(f"Device {device_id} successfully updated blockchain")

                        print("Resolved Blockchain: ")
                        for block in resolved_chain:
                            print(f"Block {block['index']}:\n")
                            print(f"Timestamp: {block['timestamp']}\n")
                            print(f"Previous Hash: {block['previous_hash']}\n")
                            print(f"Proof: {block['proof']}\n")
                            print(f"Interactions: {block['interactions']}\n")
                        print("--End of Blockchain--\n")
                        
                    else:
                        print(f"Device {device_id} failed to update {response}")
            except Exception as e:
                print(f"Error updating blockchain for {device_id}: {e}")

    def consensus_protocol(self): 
        while True:
            blockchains = self.request_blockchains()
            resolved_chain = self.solve_conflicts(blockchains)
            self.update_devices(resolved_chain)
            time.sleep(30) #run protocol every 60 seconds after started 

    #the idea is to have a button to trigger consensus protocol to work every 60sec once all devices are registered via the UI
    def start_consensus_protocol(self): #to run consensus protocol on its own thread once all devices have been registered
        consensus_thread = threading.Thread(target=self.consensus_protocol)
        consensus_thread.daemon = True
        consensus_thread.start()

    def send(self, message, recipient):
        """Send message to a device via TCP"""
        try:
            device_id = self.get_device_id(recipient[0], recipient[1])

            # First encrypt the message
            encrypted_message = self.encrypt(message)
            
            # Generate MAC for encrypted message
            mac = self.generate_mac(encrypted_message)
            
            # Combine encrypted message and MAC
            message_with_mac = f"{encrypted_message} | {mac}"

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
            logging.info(f"Sending encrypted command to device '{device_id}' at {recipient}")

            with socket.socket(AF_INET, SOCK_STREAM) as s:
                s.connect(recipient)
                s.sendall(message_with_mac.encode("utf-8"))
                logging.info(f"Encrypted message sent to device '{device_id}'")
                print(f"Sent encrypted message to {device_id}")

        except Exception as e:
            logging.error(f"Error sending message to device at {recipient}: {e}")
            print(f"Error sending message: {e}")
            raise

    def receive(self):
        """Receive message from a device via TCP"""
        try:
            conn, addr = self.commSocket.accept()
            data = conn.recv(self._buf).decode("utf-8")

            # Split message and MAC
            if "|" in data:
                encrypted_message, mac = data.rsplit("|", 1)
                encrypted_message = encrypted_message.strip()
                mac = mac.strip()

                # Verify MAC
                if not hmac.compare_digest(self.generate_mac(encrypted_message), mac):
                    raise ValueError("Invalid MAC")

                # Decrypt the message after MAC verification
                plain_text = self.decrypt(encrypted_message)
            else:
                raise ValueError("Invalid message format")

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
            logging.info(f"Decrypted message received from device '{device_id}': {plain_text}")
            print(f"Received decrypted message from {device_id}: {plain_text}")
            conn.close()
            return plain_text, addr

        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            print(f"Error receiving message: {e}")