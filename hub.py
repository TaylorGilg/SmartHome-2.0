import logging
from communicator import Communicator
from socket import *
import threading
import time
import io
from PIL import Image
import traceback
from data.config import *
#from blockchain import Blockchain, Block #import block chain classes

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
        self._authenticated_devices = {} # {device_id: (ip, port)}
        self._device_locations = {}       # {device_id: location}
        self._ip_to_id = {}               # {(ip, port): device_id}
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

    def init_sockets(self):
        """Creates a socket. For initialization."""
        super().init_sockets(self._ip, self._port)
        logging.info(f"Sockets initialized for Hub '{self.name}' at {self._ip}:{self._port}")
        return
    
    def send(self, message, recipient):
        """Send message to a device"""
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
            
            # Format and send message
            if not isinstance(message, bytes) and not message.startswith(("text:", "image:")):
                message = "text:" + str(message)
                
            cipher_text = self.encrypt(message).encode("utf-8")
            self.commSocket.sendto(cipher_text, recipient)
            logging.info(f"Message sent to device '{device_id}': {message}")
            print(f"Sent message to {device_id}: {message}")
            
        except Exception as e:
            logging.error(f"Error sending message to device at {recipient}: {e}")
            print(f"Error sending message: {e}")
            raise

    def receive(self):
        """Receive message from a device"""
        try:
            data, addr = self.commSocket.recvfrom(self._buf)
            msg = str(data, "utf-8")
            plain_text = self.decrypt(msg)
            
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
            return plain_text, addr
            
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            print(f"Error receiving message: {e}")

    # Blockchain Consensus Protocol

    #hub requests blockchain state from each device via a TCP connection (more reliable than UDP)
    def request_blockchains(self):
        blockchains = {} #dictionary of blockchain data with corresponding device_id as key
        #loops through authenticated devices and establishes TCP connection
        for device_id, (device_ip, device_port) in self.authenticated_devices.items():
            try:
                #"with" ensures socket closes after use 
                #creates a TCP socket (AF_INET specifies IPv4, SOCK_STREAM specifies TCP)
                with socket(AF_INET, SOCK_STREAM) as s: 
                    #connects socket to device's ip and port
                    s.connect((device_ip, device_port)) 
                    #sends request message for command to get blockchain data of device
                    s.sendall(b"GET_BLOCKCHAIN_DATA")
                    #waits for response back (recv reads up to 4095 bytes from the socket)
                    response = s.recv(4096)
                    #parses and stores data in dictionary with device_id as key
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

    #takes in longest valid chain to and updates ledgers of all authenticated devices to match
    def update_devices(self, resolved_chain):
        #iterating over every authenticated device
        for device_id, (device_ip, device_port) in self._authenticated_devices.items():
            try: 
                #up to 3 tries to resend data for successful update
                retries = 3
                while retries > 0:
                    #sending message to device to update blockchain with resolved chain
                    self.send(f"update_blockchain;{json.dumps(resolved_chain)}", (device_ip, device_port))
                    #waits for an acknowledgment response (successfully updated) from device (stops waiting after 5 sec)
                    ack, _= self.recieve(timeout=5)
                    if ack == "ACK":
                        break
                    retries -= 1
                if retries == 0:
                    print(f"{device_id} failed to update after multiple tries.")
            except Exception as e: 
                print(f"Error updating blockchain for {device_id}: (e)")

    def consensus_protocol(self):
        while True:
            #calls method to request blockchain state of all devices 
            blockchains = self.request_blockchains()
            #calls method to resolve differing ledgers
            resolved_chain = self.solve_conflicts(blockchains)
            #calls method to update all devices with consensus
            self.update_devices(resolved_chain)
            #runs this method every 60 sec
            time.sleep(60) 


