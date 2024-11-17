from communicator import Communicator
from socket import *
from blockchain import Blockchain
import time

class IOTDevice(Communicator):
    def __init__(self, id, device_type="unknown", location="unknown"):
        super().__init__(id)
        self.device_type = device_type
        self.location = location
        print(f"Initializing {device_type} device {id} at location: {location}")

    def send(self, message, recipient, data_type=None, TCP_socket=None, server_addr=None):
        """Enhanced send method with device identification"""
        try:
            # Log the outgoing message
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
            if data_type == 'image':            
                header = data_type + ":" + str(len(message))
                cipher_header = self.encrypt(header).encode("utf-8")
                self.commSocket.sendto(cipher_header, recipient)
                
                response = self.receive()
                if response[0] == 'ack':
                    TCP_socket.connect(server_addr)
                    TCP_socket.sendall(message)
                
                response = self.receive()
                if response[0] == 'done':
                    TCP_socket.close()
            else:
                # Format message
                if not isinstance(message, bytes) and not message.startswith(("text:", "image:")):
                    message = "text:" + str(message)
                
                cipher_text = self.encrypt(message).encode("utf-8")
                self.commSocket.sendto(cipher_text, recipient)
                print(f"{self.device_type} {self.id} sent: {message}")
            
        except Exception as e:
            print(f"Error in send for {self.device_type} {self.id}: {e}")
            raise

    def receive(self):
        """Enhanced receive method with device identification"""
        try:
            data, addr = self.commSocket.recvfrom(self.buf)
            msg = str(data, "utf-8")
            plain_text = self.decrypt(msg)
                
            if plain_text.startswith("text:"):
                plain_text = plain_text[5:]
                
            # Log the incoming message
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
            print(f"Error in receive for {self.device_type} {self.id}: {e}")
            return f"Error: {str(e)}", addr

    def init_sockets(self, ip, port):
        """Initialize device sockets with better logging"""
        try:
            self.setIP(ip)
            self.setPort(port)
            UDP_socket = socket(AF_INET, SOCK_DGRAM)
            UDP_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            UDP_socket.bind((self.ip, self.port))
            self.setSocket(UDP_socket)
            print(f"{self.device_type} {self.id} initialized socket on {ip}:{port}")
        except Exception as e:
            print(f"Error initializing socket for {self.device_type} {self.id}: {e}")
            raise

    def parse_command(self, command):
        """Enhanced command parsing with better error handling"""
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
        """Get device location"""
        return f"{self.device_type} {self.id} location: {self.location}"
    
    def set_location(self, new_location):
        """Set device location"""
        self.location = new_location
        return f"{self.device_type} {self.id} location set to {new_location}"
    
    def get_info(self):
        """Get device information"""
        return {
            "id": self.id,
            "type": self.device_type,
            "location": self.location,
            "ip": self.ip,
            "port": self.port
        }
        
        return new_command, message
    
    #takes in resolved chain to update personal device ledger 
    def update_blockchain(self, chain_data):
        try:
            #parsing input
            new_chain = json.loads(chain_data)
            #checks if new chain has all valid block hashes and proof of work
            if self.blockchain.is_valid_chain(new_chain):
                #replaces old blockchain with new one
                self.blockchain.chain = new_chain
                return "Blockchain update successfully"
            else:
                return "Recieved invalid blockchain"
        except Exception as e:
            return f"Error updating blockchain: {str(e)}"
        
    


