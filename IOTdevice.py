import logging
from communicator import Communicator
from socket import *
import json
import time
from Blockchain import Blockchain

class IOTDevice(Communicator):
    def __init__(self, id, device_type="unknown", location="unknown"):
        super().__init__(id)
        self.device_type = device_type
        self.location = location
        self.tcp_port = None
        self.blockchain = Blockchain()
        
        print(f"Initializing {self.device_type} device {self.id} at location: {self.location}")
        
    def display_blockchain(self):
        """Print blockchain into a txt file"""
        try:
            with open(f"{self.device_type}_{self.id}_blockchain.txt", "w") as file:
                file.write(f"Blockchain for {self.device_type} ({self.id}):\n")
                for block in self.blockchain.chain:
                    file.write(f"\nBlock {block['index']}:\n")
                    file.write(f"Timestamp: {block['timestamp']} \n")
                    file.write(f"Previous Hash: {block['previous_hash']} \n")
                    file.write(f"Proof: {block['proof']} \n")
                    file.write(f"Interactions: {block['interactions']} \n")
                file.write("\nEnd of blockchain.\n")
        except Exception as e:
            print(f"Error writing blockchain to file: {e}")
        
    def start_TCP(self):
        """Starts a TCP server for blockchain consensus protocol"""
        try:
            TCP_socket = socket(AF_INET, SOCK_STREAM)
            TCP_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            TCP_socket.bind(("0.0.0.0", self.tcp_port))
            TCP_socket.listen(5)
            print(f"{self.device_type} {self.id} listening for TCP connections on {self.ip}:{self.tcp_port}")

            while True:
                conn, addr = TCP_socket.accept()
                try:
                    request = conn.recv(4096).decode("utf-8")
                    if not request:
                        print(f"Empty request from {addr}.")
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
                    print(f"Error handling TCP request from {addr}: {e}")
                finally:
                    conn.close()
        except Exception as e:
            print(f"Error starting TCP server for {self.device_type} {self.id}: {e}")
            raise

    def send(self, message, recipient):
        """Send encrypted message and log to blockchain"""
        try:
            # Log the outgoing message to blockchain
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
            
            # Use parent's encrypted send
            super().send(message, recipient)
            print(f"{self.device_type} {self.id} sent: {message} to {recipient}")
            
        except Exception as e:
            print(f"Error in send for {self.device_type} {self.id}: {e}")
            raise

    def receive(self):
        """Receive encrypted message and log to blockchain"""
        try:
            # Use parent's encrypted receive
            message, addr = super().receive()
            
            if not message:
                raise ValueError("Received empty data.")

            # Log the received message to blockchain
            self.blockchain.new_interaction(
                sender=str(addr),
                recipient=f"{self.device_type}:{self.id}",
                data={
                    "type": "command",
                    "message": message,
                    "location": self.location,
                    "timestamp": time.time(),
                    "status": "received"
                }
            )
            print(f"{self.device_type} {self.id} received: {message}")
            return message, addr
        except Exception as e:
            print(f"Error in receive for {self.device_type} {self.id}: {e}")
            raise

    def init_sockets(self, ip, port):
        """Initialize main socket and TCP port for blockchain"""
        try:
            self.setIP(ip)
            self.setPort(port)
            # Set up TCP port for blockchain consensus
            self.tcp_port = port + 1000
            
            # Initialize main communication socket
            self.commSocket = socket(AF_INET, SOCK_STREAM)
            self.commSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.commSocket.bind((self.ip, self.port))
            self.commSocket.listen(5)
            print(f"{self.device_type} {self.id} initialized TCP socket on {ip}:{self.tcp_port}")
        except Exception as e:
            print(f"Error initializing socket for {self.device_type} {self.id}: {e}")
            raise

    def parse_command(self, command):
        """Parse incoming commands"""
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
            
            print(f"{self.device_type} {self.id} parsing command: {new_command} with message: {message}")
            return new_command, message
            
        except Exception as e:
            print(f"Error parsing command for {self.device_type} {self.id}: {e}")
            return "error", str(e)

    def get_location(self):
        return f"{self.device_type} {self.id} location: {self.location}"

    def set_location(self, new_location):
        self.location = new_location
        return f"{self.device_type} {self.id} location set to {new_location}"

    def update_blockchain(self, chain_data): 
        """Update blockchain during consensus"""
        try:
            new_chain = json.loads(chain_data)
            if self.blockchain.is_valid_chain(new_chain):
                self.blockchain.chain = new_chain
                with open(f"{self.device_type}_{self.id}_blockchain.txt", "a") as file:
                    file.write(f"Consensus Protocol Result:\n")
                self.display_blockchain()
                return "ACK: Blockchain update successful"
            else:
                with open(f"{self.device_type}_{self.id}_blockchain.txt", "a") as file:
                    file.write(f"{self.device_type} {self.id}: Received invalid blockchain.")
                return "Error: Received invalid blockchain"
        except Exception as e:
            with open(f"{self.device_type}_{self.id}_blockchain.txt", "a") as file:
                file.write(f"{self.device_type} {self.id}: Error updating blockchain: {e}")
            return f"Error updating blockchain: {str(e)}"