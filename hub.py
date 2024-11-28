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

        # setting up log file for testing blockchain ledgers
        self.logger = logging.getLogger("Hub")
        file_handler = logging.FileHandler("hub_blockchain_log.txt")
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(file_handler)
        self.logger.setLevel(logging.INFO)

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

    def send(self, message, recipient):
        """Send message to a device via TCP"""
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

            with socket(AF_INET, SOCK_STREAM) as s:
                s.connect(recipient)
                s.sendall(message.encode("utf-8"))
                logging.info(f"Message sent to device '{device_id}': {message}")
                print(f"Sent message to {device_id}: {message}")

        except Exception as e:
            logging.error(f"Error sending message to device at {recipient}: {e}")
            print(f"Error sending message: {e}")
            raise

    def receive(self):
        """Receive message from a device via TCP"""
        try:
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

    def update_devices(self, resolved_chain):
        """Send resolved blockchain data to devices via TCP"""
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

    def consensus_protocol(self):
        """Run the blockchain consensus protocol"""
        while True:
            self.logger.info("Starting consensus protocol...")
            blockchains = self.request_blockchains()
            resolved_chain = self.solve_conflicts(blockchains)
            self.update_devices(resolved_chain)
            self.logger.info("Consensus protocol completed.")

            # Log the resolved blockchain
            self.logger.info("Consensus Result: ")
            with open("hub_blockchain_log.txt", "a") as file:
                for block in resolved_chain:
                    file.write(f"Block {block['index']}:\n")
                    file.write(f"Timestamp: {block['timestamp']}\n")
                    file.write(f"Previous Hash: {block['previous_hash']}\n")
                    file.write(f"Proof: {block['proof']}\n")
                    file.write(f"Interactions: {block['interactions']}\n")
                file.write("\n")

            time.sleep(60)  # Run every 60 seconds