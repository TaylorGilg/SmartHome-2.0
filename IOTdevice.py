from communicator import Communicator
import time
from socket import *

class IOTDevice(Communicator):
    def __init__(self, id):
        super().__init__(id)

    def send(self, message, recipient, data_type=None, TCP_socket=None, server_addr=None):
        """
        Enhanced send method with proper message formatting
        """
        try:
            # Format message based on type
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
                # Log the outgoing message
                self.blockchain.new_interaction(
                    sender=self.id,
                    recipient=str(recipient),
                    data={
                        "type": "response",
                        "message": message,
                        "timestamp": time.time(),
                        "status": "sent"
                    }
                )
                
                # Don't add prefix if message already has one
                if not isinstance(message, bytes) and not message.startswith(("text:", "image:")):
                    message = "text:" + str(message)
                
                cipher_text = self.encrypt(message).encode("utf-8")
                self.commSocket.sendto(cipher_text, recipient)
        except Exception as e:
            print(f"Error in send: {e}")
            raise

    def receive(self):
        """
        Enhanced receive method with proper message handling
        """
        try:
            data, addr = self.commSocket.recvfrom(self.buf)
            msg = str(data, "utf-8")
            plain_text = self.decrypt(msg)
            
            # Remove prefix if exists
            if plain_text.startswith("text:"):
                plain_text = plain_text[5:]
            
            # Log the incoming message
            self.blockchain.new_interaction(
                sender=str(addr),
                recipient=self.id,
                data={
                    "type": "command",
                    "message": plain_text,
                    "timestamp": time.time(),
                    "status": "received"
                }
            )
            
            return plain_text, addr
        except Exception as e:
            print(f"Error in receive: {e}")
            return f"Error: {str(e)}", addr

    def parse_command(self, command):
        """
        Enhanced command parsing
        """
        try:
            if isinstance(command, tuple):
                command = command[0]  # Extract command if it's a tuple
                
            if command.startswith("Error"):
                return "error", command
                
            parts = command.split(';')
            new_command = parts[0].strip()
            message = parts[1].strip() if len(parts) > 1 else None
            
            return new_command, message
        except Exception as e:
            print(f"Error parsing command: {e}")
            return "error", str(e)

    def init_sockets(self, ip, port):
        """
        Initialize device sockets
        """
        self.setIP(ip)
        self.setPort(port)
        UDP_socket = socket(AF_INET, SOCK_DGRAM)
        UDP_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        UDP_socket.bind((self.ip, self.port))
        self.setSocket(UDP_socket)