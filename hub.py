import logging
from communicator import Communicator
from socket import *
import threading
import time
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
        self.name = name
        self._authenticated_devices = {}
        self._device_locations = {}
        self._ip_to_id = {}
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
        return self._ip_to_id.get((ip, int(port)), f"{ip}:{port}")

    def get_device_location(self, device_id):
        location = self._device_locations.get(device_id, "unknown")
        logging.info(f"Retrieved location for device '{device_id}': {location}")
        return location

    def get_device_status(self):
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
        """Initialize TCP socket"""
        try:
            self.commSocket = socket(AF_INET, SOCK_STREAM)
            self.commSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.commSocket.bind((self._ip, self._port))
            self.commSocket.listen(5)
            logging.info(f"Hub '{self.name}' TCP socket initialized at {self._ip}:{self._port}")
        except Exception as e:
            logging.error(f"Error initializing sockets: {e}")
            raise

    def request_blockchains(self):
        """Request blockchain data from devices via TCP"""
        blockchains = {}
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

    def solve_conflicts(self, blockchains):
        longest_chain = None
        max_length = 0
        best_cumulative_proof = 0

        for device_id, chain in blockchains.items():
            try:
                if self.blockchain.is_valid_chain(chain) and len(chain) >= max_length:
                    cumulative_proof = sum(block['proof'] for block in chain)
                    if (len(chain) > max_length or 
                        (len(chain) == max_length and cumulative_proof > best_cumulative_proof)):
                        longest_chain = chain
                        max_length = len(chain)
                        best_cumulative_proof = cumulative_proof
            except Exception as e:
                print(f"Error validating chain from {device_id}: {e}")

        return longest_chain if longest_chain is not None else self.blockchain.chain

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

    def consensus_protocol(self):
        while True:
            blockchains = self.request_blockchains()
            resolved_chain = self.solve_conflicts(blockchains)
            self.update_devices(resolved_chain)
            time.sleep(60)

    def start_consensus_protocol(self):
        consensus_thread = threading.Thread(target=self.consensus_protocol)
        consensus_thread.daemon = True
        consensus_thread.start()

def start_hub(name):
    """Main hub control loop with proper encryption"""
    try:
        print("Setting up a new Hub..")
        hub = Hub(name, HUB_IP, HUB_PORT)
        hub.setEncryption(KEY, upperCaseAll=False, removeSpace=False)
        hub.init_sockets()

        # Start consensus protocol
        hub.start_consensus_protocol()
        
        print(f"Hub '{hub.name}' running at {HUB_IP}:{HUB_PORT}")
        
        while True:
            try:
                # Use parent Communicator's receive method which handles encryption
                message, addr = hub.receive()
                device_id = hub.get_device_id(addr[0], addr[1])
                
                if message == "exit":
                    break
                    
                command, msg = hub.parse_command(message)
                output = f"Command processed: {command}"
                
                # Use parent Communicator's send method which handles encryption
                hub.send(output, addr)
                
            except Exception as e:
                error_msg = f"Error in Hub: {str(e)}"
                logging.error(error_msg)
                print(error_msg)
                continue

    except Exception as e:
        logging.critical(f"Fatal error in Hub: {str(e)}")
    finally:
        logging.info("Hub shutting down...")

if __name__ == "__main__":
    start_hub("HUB")