from Vigenere import VigenereCipher
from Caesar import CaesarCipher
from Blockchain import Blockchain
import time
from socket import *
import hmac
import hashlib
import json

class Communicator:
# Base communication class that facillitates
# 1. TCP socket communication
# 2. Message encryption/decryption
# 3. Blockchain logging of all communications
# 4. Command parsing
# This serves as the foundation for all IoT device communcation in our network.
    
    def __init__(self, id):
        self.id = id
        # TCP connection properties
        self.ip = None
        self.port = None
        self.commSocket = None
        # Encryption settings
        self.cipher = None
        self.enableEncryption = False
        self.buf = 1024
        # Initialize blockchain for logging all communications
        self.blockchain = Blockchain()
        self.mac_key = b"super_secret_key"  # Shared key for HMAC
        print(f"Communicator initialized with ID: {id}")

    # MAC Generation
    def generate_mac(self, message):
        """Generates an HMAC for the given message"""
        h = hmac.new(self.mac_key, message.encode(), hashlib.sha256)
        return h.hexdigest()

    # MAC Verification
    def verify_mac(self, message, mac):
        """Verifies the HMAC for the given message"""
        return hmac.compare_digest(self.generate_mac(message), mac)

    def encrypt(self, message):
        if self.enableEncryption: 
            encrypted_message = self.cipher.encrypt(message)
            return encrypted_message
        else:
            return message

    def decrypt(self, encrypted_message):
        if self.enableEncryption:
            decrypted_message = self.cipher.decrypt(encrypted_message)
            return decrypted_message
        else:
            return encrypted_message

# Send a message via TCP and log it to blockchain. This provides both communication and an immutable record.
    def send(self, message, recipient):
        """Send message using TCP"""
        try:
            # Generate MAC and append it to the message
            mac = self.generate_mac(message)
            message_with_mac = f"{message} | {mac}"

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
            # Create new block with proof of work
            proof = self.blockchain.proof_of_work(self.blockchain.last_block['proof'])
            self.blockchain.new_block(proof)

            #display the blockchain
            self.display_blockchain()

            # Format message
            if not isinstance(message, bytes):
                message = "text:" + str(message)
            
            # Encrypt message
            cipher_text = self.encrypt(message_with_mac).encode("utf-8")

            # Open a TCP connection and send the message
            with socket.socket(AF_INET, SOCK_STREAM) as s:
                s.connect(recipient)
                s.sendall(cipher_text)
                print(f"Sent message: {message} to {recipient}")
            
        except Exception as e:
            print(f"Error in send: {e}")
            raise

    # Receive and log incoming TCP messages. Each received message is decrypted and logged to blockchain.
    def receive(self):
        """Receive message using TCP"""
        try:
            conn, addr = self.commSocket.accept()  # Accept an incoming connection
            data = conn.recv(self.buf)  # Receive raw encrypted data
            decoded_data = data.decode("utf-8")  # Decode from bytes
            plain_text = self.decrypt(decoded_data)  # Decrypt the message

            # Split message and MAC
            if "|" in decrypted_message:
                plain_text, mac = decrypted_message.rsplit("|", 1)

                # Verifty the MAC
                if not self.verify_mac(plain_text, mac):
                    raise ValueError("Invalid MAC. Message integrity check failed.")
            else:
                raise ValueError("Message format invalid: Missing MAC.")

            # Remove text: prefix if present
            if plain_text.startswith("text:"):
                plain_text = plain_text[5:]
            
            # Log received message to blockchain
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
            proof = self.blockchain.proof_of_work(self.blockchain.last_block['proof'])
            self.blockchain.new_block(proof)

            #display the blockchain
            self.display_blockchain()
            
            print(f"Received message: {plain_text} from {addr}")
            conn.close()
            return plain_text, addr

        except Exception as e:
            print(f"Error in receive: {e}")
            return f"Error: {str(e)}", None
        
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
        
    # Initialize TCP socket for device communication.
    def init_sockets(self, ip, port):
        """Initialize TCP socket"""
        try:
            self.setIP(ip)
            self.setPort(port)

            # Create and bind the TCP socket
            self.commSocket = socket.socket(AF_INET, SOCK_STREAM)
            self.commSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.commSocket.bind((self.ip, self.port))
            self.commSocket.listen(5)  # Listen for incoming connections
            print(f"Socket initialized and listening on {ip}:{port}")

        except Exception as e:
            print(f"Error initializing socket: {e}")
            raise

# Format blockchain data for UI display. Shows complete history of all device communications.
    def get_blockchain_data(self, device_id=None):
        """Returns formatted blockchain data for UI display or analysis"""
        try:
            #if device_id is provided, get blockchain for specific device
            if device_id:
                if device_id not in self._authenticated_devices:
                    raise ValueError(f"Device {device_id} not found")
            
                device_ip, device_port = self._authenticated_devices[device_id]
                blockchain_data = self.request_blockchain_from_device(device_ip, device_port)
            else:
                blockchain = self.blockchain.chain

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
    
    def request_blockchain_from_device(self, device_ip, device_port):
        #request blockchain data from specific device
        try:
            with socket.socket(AF_INET, SOCK_STREAM) as s:
                s.connect((device_ip, device_port))
                s.sendall(b"GET_BLOCKCHAIN_DATA")
                response = s.recv(4096)
                return json.loads(response)
        except Exception as e:
            print(f"Error requesting blockchain data from {device_ip}:{device_port}: {e}")
            return []

   # Check if our blockchain is valid and hasn't been tampered with
    def verify_blockchain(self):
        """Verifies the integrity of the blockchain"""
        try:
            return self.blockchain.is_valid_chain()
        except Exception as e:
            print(f"Error verifying blockchain: {e}")
            return False

    # Setters for our configuration methods.
    def setIP(self, ipaddr):
        self.ip = ipaddr

    def setPort(self, portNumber):
        self.port = portNumber

    def setEncryption(self, key,
        removeSpace=True,          # Remove space
        encryptSpace=False,         # Encrypt Space
        encryptSymbol=False,        # Encrypt Symbol
        upperCaseAll=True,        # Uppercase ALL
        reverseText=False         # Reverse Plain text
    ):
        """Configure encryption settings"""
        try:
            self.enableEncryption = True
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

    def display_blockchain(self):
        """Display blockchain to file for monitoring"""
        try:
            with open(f"{self.id}_blockchain.txt", "w") as f:
                for block in self.blockchain.chain:
                    f.write(f"\nBlock {block['index']}:\n")
                    f.write(f"Timestamp: {time.ctime(block['timestamp'])}\n")
                    f.write(f"Previous Hash: {block['previous_hash']}\n")
                    f.write(f"Proof: {block['proof']}\n")
                    f.write("Interactions:\n")
                    for interaction in block['interactions']:
                        f.write(f"From: {interaction['sender']}\n")
                        f.write(f"To: {interaction['recipient']}\n")
                        f.write(f"Data: {interaction['data']}\n")
                        f.write("-" * 50 + "\n")
        except Exception as e:
            print(f"Error displaying blockchain: {e}")

    def process_command(self):
        """Base method for command processing"""
        pass
        
    def compress_img(self, img_data):
        """Placeholder for image compression logic"""
        return img_data
    
    def decompress_img(self, compress_data):
        """Placeholder for image decompression logic"""
        return compress_data