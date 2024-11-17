from Vigenere import VigenereCipher
from Caesar import CaesarCipher
from blockchain import Blockchain
import time
from socket import *

class Communicator:
    
    def __init__(self, id):
        self.id = id
        self.ip = None
        self.port = None
        self.commSocket = None
        self.cipher = None
        self.enableEncyption = False
        self.buf = 512
        self.blockchain = Blockchain()
        print(f"Communicator initialized with ID: {id}")

    def encrypt(self, message):
        if self.enableEncyption: 
            encrypted_message = self.cipher.encrypt(message)
            return encrypted_message
        else:
            return message

    def decrypt(self, encrypted_message):
        if self.enableEncyption:
            decrypted_message = self.cipher.decrypt(encrypted_message)
            return decrypted_message
        else:
            return encrypted_message

    def send(self, message, recipient, data_type=None, TCP_socket=None, server_addr=None):
        """Enhanced send method"""
        try:
            # Log the outgoing message
            self.blockchain.new_interaction(
                sender=self.id,
                recipient=str(recipient),
                data={
                    "type": "outgoing_message",
                    "message": str(message),
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
                
                # Encrypt and send
                cipher_text = self.encrypt(message).encode("utf-8")
                self.commSocket.sendto(cipher_text, recipient)
                print(f"Sent message: {message} to {recipient}")
        except Exception as e:
            print(f"Error in send: {e}")
            raise
                
        except Exception as e:
                print(f"Error in send: {e}")
                raise


    def receive(self):
        """Enhanced receive method"""
        try:
            data, addr = self.commSocket.recvfrom(self.buf)
            msg = str(data, "utf-8")
            plain_text = self.decrypt(msg)
            
            # Remove text: prefix if present
            if plain_text.startswith("text:"):
                plain_text = plain_text[5:]
            
            # Log the incoming message
            self.blockchain.new_interaction(
                sender=str(addr),
                recipient=self.id,
                data={
                    "type": "incoming_message",
                    "message": plain_text,
                    "timestamp": time.time(),
                    "status": "received"
                }
            )
            
            print(f"Received message: {plain_text} from {addr}")
            return plain_text, addr
            
        except Exception as e:
            print(f"Error in receive: {e}")
            return f"Error: {str(e)}", addr
        
    def parse_command(self, command):
        """Parse received command from Hub"""
        try:
            # Handle tuple input
            if isinstance(command, tuple):
                command = command[0]
                
            # Handle error messages
            if isinstance(command, str) and command.startswith("Error"):
                return "error", command
                
            # Remove text: prefix if present
            if command.startswith("text:"):
                command = command[5:]
                
            # Split into command and message
            parts = command.split(';')
            new_command = parts[0].strip()
            message = parts[1].strip() if len(parts) > 1 else None
            
            print(f"Parsed command '{new_command}' with message '{message}'")
            return new_command, message
            
        except Exception as e:
            print(f"Error parsing command: {e}")
            return "error", str(e)
        
    def init_sockets(self, ip, port):
        """Initialize socket"""
        try:
            self.setIP(ip)
            self.setPort(port)
            UDP_socket = socket(AF_INET, SOCK_DGRAM)
            UDP_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
            UDP_socket.bind((self.ip, self.port))
            self.setSocket(UDP_socket)
            print(f"Socket initialized on {ip}:{port}")

        except Exception as e:
            print(f"Error initializing socket: {e}")
            raise

    def get_blockchain_data(self):
        """Returns formatted blockchain data for UI display or analysis"""
        try:
            blockchain_data = []
            for block in self.blockchain.chain:
                block_data = {
                    "index": block['index'],
                    "timestamp": time.ctime(block['timestamp']),
                    "proof": block['proof'],
                    "previous_hash": block['previous_hash'],
                    "interactions": block['interactions']
                }
                blockchain_data.append(block_data)
            return blockchain_data
        
        except Exception as e:
            print(f"Error getting blockchain data: {e}")
            return []

    def verify_blockchain(self):
        """Verifies the integrity of the blockchain"""
        try:
            return self.blockchain.is_valid_chain()
        except Exception as e:
            print(f"Error verifying blockchain: {e}")
            return False

    # setters
    def setIP(self, ipaddr):
        self.ip = ipaddr

    def setPort(self, portNumber):
        self.port = portNumber

    def setSocket(self, socket):
        self.commSocket = socket
        
    def setEncryption(self, key,
        removeSpace=True,          # Remove space
        encryptSpace=False,         # Encrypt Space
        encryptSymbol=False,        # Encypt Symbol
        upperCaseAll=True,        # Uppercase ALL
        reverseText = False    # Reverse Plain text
    ):
        try:
            self.enableEncyption = True
            self.cipher = CaesarCipher(key)
            self.cipher.removeSpace = removeSpace
            self.cipher.encryptSpace = encryptSpace
            self.cipher.upperCaseAll = upperCaseAll
            self.cipher.reverseText = reverseText
            self.cipher.encryptSymbol = encryptSymbol
            print("Encryption settings configured")

        except Exception as e:
            print(f"Error setting encryption: {e}")
            raise

    def process_command(self):
        """Base method for command processing"""
        pass
        
    def compress_img(self, img_data):
        return img_data
    
    def decompress_img(self, compress_data):
        return compress_data
