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
        
    def display_blockchain(self): # print blockchain into a txt file
        with open(f"{self.device_type}_{self.id}_blockchain.txt", "w") as file:
            file.write(f"Blockchain for {self.device_type} ({self.id}):\n")
        for block in self.blockchain.chain:
            file.write(f"Block {block['index']}:\n")
            file.write(f"Timestamp: {block['timestamp']} \n")
            file.write(f"Previous Hash: {block['previous_hash']} \n")
            file.write(f"Proof: {block['proof']} \n")
            file.write(f"Interactions: {block['interactions']} \n")
        file.write("End of blockchain.\n")
        
# Starts a new TCP server for thje blockchain ledger. TCP ports are assigned as 1000 over the port device is running on to avoid port conflicts and handles two things in particular: Sends a copy of the blockchain to who asks and update if someone sends us a better one.
    def start_TCP(self):
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
                    self.logger.error(f"Error handling TCP request from {addr}: {e}")
                finally:
                    conn.close()
        except Exception as e:
            self.logger.error(f"Error starting TCP server for {self.device_type} {self.id}: {e}")
            raise

# First log the outgoing message in the blockchain bvefore sending. Creates a new interaction with metadata like timestamps and location.
    def send(self, message, recipient):
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
            # Actually sends the message with the TCP socket and ensures it gracefully closes in the presence of errors.
            with socket(AF_INET, SOCK_STREAM) as tcp_socket:
                tcp_socket.connect(recipient)
                tcp_socket.sendall(message.encode("utf-8"))
                print(f"{self.device_type} {self.id} sent: {message} to {recipient}")
        except Exception as e:
            self.logger.error(f"Error in send for {self.device_type} {self.id}: {e}")
            raise

# Receives a message from another device and logs it in the blockchain
    def receive(self):
        try:
            # Wait for the connection to be established before retriving 4096 bytes buffer.
            conn, addr = self.commSocket.accept()
            data = conn.recv(4096).decode("utf-8")
            if not data:
                raise ValueError("Received empty data.")
            # Decrypt the message using included encryption ciphers.
            plain_text = self.decrypt(data)
            # Rudimentary text handling for when a device recieves the command and needs trimming.
            if plain_text.startswith("text:"):
                plain_text = plain_text[5:]
                # Logging the recieved command into the blockchain.
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
            print(f"{self.device_type} {self.id} received: {plain_text}")
            return plain_text, addr
        except Exception as e:
            self.logger.error(f"Error in receive for {self.device_type} {self.id}: {e}")
            raise

# Sets up tweo ports for the device to run, a regular port for device commands to be recieved and processed, and another port+1000 for blockchain consensus usage.
    def init_sockets(self, ip, port):
        try:
            self.setIP(ip)
            self.setPort(port)
            # To avoid conflicts we are setting up a TCP socket = 1000 for blockchain commands besides our regular control logic commands.
            self.tcp_port = port + 1000
            self.commSocket = socket(AF_INET, SOCK_STREAM)
            self.commSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.commSocket.bind((self.ip, self.port))
            self.commSocket.listen(5)
            print(f"{self.device_type} {self.id} initialized TCP socket on {ip}:{self.tcp_port}")
        except Exception as e:
            self.logger.error(f"Error initializing socket for {self.device_type} {self.id}: {e}")
            raise

# Parses incoming commands in the format provided by the documentation
    def parse_command(self, command):
        try:
            # Handling of tuple input
            if isinstance(command, tuple):
                command = command[0]
                # Checking for error messages that are appended.
            if isinstance(command, str) and command.startswith("Error"):
                return "error", command
            # Remove the text prefix
            if command.startswith("text:"):
                command = command[5:]
                # Split our commands so we can properly decipher them.
            parts = command.split(';')
            new_command = parts[0].strip()
            message = parts[1].strip() if len(parts) > 1 else None
            print(f"{self.device_type} {self.id} parsing command: {new_command} with message: {message}")
            return new_command, message
        except Exception as e:
            self.logger.error(f"Error parsing command for {self.device_type} {self.id}: {e}")
            return "error", str(e)

    def get_location(self):
        return f"{self.device_type} {self.id} location: {self.location}"

    def set_location(self, new_location):
        self.location = new_location
        return f"{self.device_type} {self.id} location set to {new_location}"

    # Updates the device's blockchain when hub sends a new version - serves as part of the consesus protocol where we can keep our devices in sync with one another.
    def update_blockchain(self, chain_data): 
        try:
            # Data conversion from JSON to Python objects 
            new_chain = json.loads(chain_data)
            # Ensure validity of the chain before we accepting it as a new addition 
            if self.blockchain.is_valid_chain(new_chain):
                self.blockchain.chain = new_chain
                with open(f"{self.device_type}_{self.id}_blockchain.txt", "a") as file:
                    file.write(f"Consensus Protocol Result:\n")
                self.display_blockchain()
                return "ACK: Blockchain update successful"
            else:
                # logging of invalid chains and errors.
                with open(f"{self.device_type}_{self.id}_blockchain.txt", "a") as file:
                    file.write(f"{self.device_type} {self.id}: Received invalid blockchain.")
                return "Error: Received invalid blockchain"
        except Exception as e:
            with open(f"{self.device_type}_{self.id}_blockchain.txt", "a") as file:
                file.write(f"{self.device_type} {self.id}: Error updating blockchain: {e}")
            return f"Error updating blockchain: {str(e)}"