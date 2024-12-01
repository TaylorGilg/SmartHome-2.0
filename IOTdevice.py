import logging
import json
import time
from socket import *
from communicator import Communicator
from Blockchain import Blockchain


class IOTDevice(Communicator):
    def __init__(self, id, device_type="unknown", location="unknown"):
        super().__init__(id)
        self.device_type = device_type
        self.location = location
        self.tcp_port = None
        self.blockchain = Blockchain()

        logging.info(f"Initializing {self.device_type} device {self.id} at location: {self.location}")

    def display_blockchain(self):
        """Display blockchain details."""
        display = "\n".join([
            f"Block {block['index']} | Timestamp: {block['timestamp']} | Data: {block['data']} | Proof: {block['proof']}"
            for block in self.blockchain.chain
        ])
        logging.info(f"Blockchain Displayed:\n{display}")
        return display

    def start_TCP(self):
        """Start a TCP server for blockchain-related communication."""
        try:
            TCP_socket = socket(AF_INET, SOCK_STREAM)
            TCP_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            TCP_socket.bind(("0.0.0.0", self.tcp_port))
            TCP_socket.listen(5)
            logging.info(f"{self.device_type} {self.id} listening for TCP connections on {self.ip}:{self.tcp_port}")

            while True:
                conn, addr = TCP_socket.accept()
                try:
                    request = conn.recv(4096).decode("utf-8")
                    if not request:
                        logging.warning(f"Empty request from {addr}.")
                        continue

                    if request == "GET_BLOCKCHAIN_DATA":
                        response = json.dumps(self.blockchain.chain).encode("utf-8")
                        conn.sendall(response)
                    elif request.startswith("UPDATE_BLOCKCHAIN;"):
                        chain_data = request.split(";", 1)[1]
                        update_response = self.update_blockchain(chain_data)
                        conn.sendall(update_response.encode("utf-8"))
                    else:
                        conn.sendall(b"Error: Unknown blockchain request")
                except Exception as e:
                    logging.error(f"Error handling TCP request from {addr}: {e}")
                finally:
                    conn.close()
        except Exception as e:
            logging.error(f"Error starting TCP server for {self.device_type} {self.id}: {e}")
            raise

    def send(self, message, recipient):
        """Send a message to a recipient."""
        try:
            self.blockchain.new_interaction(
                sender=f"{self.device_type}:{self.id}",
                recipient=str(recipient),
                data={
                    "type": "response",
                    "message": str(message),
                    "location": self.location,
                    "timestamp": time.time(),
                    "status": "sent"
                }
            )
            with socket(AF_INET, SOCK_STREAM) as tcp_socket:
                tcp_socket.connect(recipient)
                tcp_socket.sendall(message.encode("utf-8"))
                logging.info(f"{self.device_type} {self.id} sent: {message} to {recipient}")
        except Exception as e:
            logging.error(f"Error in send for {self.device_type} {self.id}: {e}")
            raise

    def receive(self):
        """Receive a message and add it to the blockchain."""
        try:
            conn, addr = self.commSocket.accept()
            data = conn.recv(4096).decode("utf-8")
            if not data:
                raise ValueError("Received empty data.")
            plain_text = self.decrypt(data)
            if plain_text.startswith("text:"):
                plain_text = plain_text[5:]
            self.blockchain.new_interaction(
                sender=str(addr),
                recipient=f"{self.device_type}:{self.id}",
                data={
                    "type": "command",
                    "message": plain_text,
                    "location": self.location,
                    "timestamp": time.time(),
                    "status": "received"
                }
            )
            logging.info(f"{self.device_type} {self.id} received: {plain_text}")
            return plain_text, addr
        except Exception as e:
            logging.error(f"Error in receive for {self.device_type} {self.id}: {e}")
            raise

    def init_sockets(self, ip, port):
        """Initialize communication sockets."""
        try:
            self.setIP(ip)
            self.setPort(port)
            self.tcp_port = port + 1000
            self.commSocket = socket(AF_INET, SOCK_STREAM)
            self.commSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.commSocket.bind((self.ip, self.port))
            self.commSocket.listen(5)
            logging.info(f"{self.device_type} {self.id} initialized TCP socket on {ip}:{self.tcp_port}")
        except Exception as e:
            logging.error(f"Error initializing socket for {self.device_type} {self.id}: {e}")
            raise

    def parse_command(self, command):
        """Parse a command and return its components."""
        try:
            if isinstance(command, tuple):
                command = command[0]
            if isinstance(command, str) and command.startswith("Error"):
                return "error", command
            if command.startswith("text:"):
                command = command[5:]
            parts = command.split(';')
            new_command = parts[0].strip()
            message = parts[1].strip() if len(parts) > 1 else None
            logging.info(f"{self.device_type} {self.id} parsing command: {new_command} with message: {message}")
            return new_command, message
        except Exception as e:
            logging.error(f"Error parsing command for {self.device_type} {self.id}: {e}")
            return "error", str(e)

    def update_blockchain(self, chain_data):
        """Update the blockchain with a new chain."""
        try:
            new_chain = json.loads(chain_data)
            if self.blockchain.is_valid_chain(new_chain):
                self.blockchain.chain = new_chain
                logging.info(f"Consensus Protocol Result: Blockchain updated successfully.")
                self.display_blockchain()
                return "ACK: Blockchain update successful"
            else:
                logging.warning(f"{self.device_type} {self.id}: Received invalid blockchain.")
                return "Error: Received invalid blockchain"
        except Exception as e:
            logging.error(f"{self.device_type} {self.id}: Error updating blockchain: {e}")
            return f"Error updating blockchain: {str(e)}"

    def get_location(self):
        return f"{self.device_type} {self.id} location: {self.location}"

    def set_location(self, new_location):
        self.location = new_location
        return f"{self.device_type} {self.id} location set to {new_location}"
