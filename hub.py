from communicator import Communicator
from socket import *
import threading
import time
import io
from PIL import Image
import traceback
from data.config import *

class Hub(Communicator):
    def __init__(self, name, ip, port):
        super().__init__(name)
        self.name = name
        self._authenticated_devices = {}  # {device_id: (ip, port)}
        self._device_locations = {}       # {device_id: location}
        self._ip_to_id = {}              # {(ip, port): device_id}
        self._ip = ip
        self._port = int(port)
        self._buf = 1024 * 2
        self.init_sockets()

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
            print(f"Device {device_id} registered at {location}")
            
        except Exception as e:
            print(f"Error registering device: {e}")
            raise

    def get_device_id(self, ip, port):
        """Get device ID from IP and port"""
        return self._ip_to_id.get((ip, int(port)), f"{ip}:{port}")

    def get_device_location(self, device_id):
        """Get device location"""
        return self._device_locations.get(device_id, "unknown")

    def init_sockets(self):
        """
        Creates a socket. For initialization.
        """
        super().init_sockets(self._ip, self._port)
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
            
            # Format and send message
            if not isinstance(message, bytes) and not message.startswith(("text:", "image:")):
                message = "text:" + str(message)
                
            cipher_text = self.encrypt(message).encode("utf-8")
            self.commSocket.sendto(cipher_text, recipient)
            print(f"Sent message to {device_id}: {message}")
            
        except Exception as e:
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
            
            print(f"Received from {device_id}: {plain_text}")
            return plain_text, addr
            
        except Exception as e:
            print(f"Error receiving message: {e}")