from communicator import Communicator
from socket import *
import threading
import time
import io
from PIL import Image
import traceback
from data.config import *
from blockchain import Blockchain, Block #import block chain classes

class Hub(Communicator):
    """
    A Hub class for managing and communicating with associated IoT devices.

    Sends and receive commands to/from IoT devices (and users).
        name:       name of this hub
        _authenticated_devices:  dict of associated devices in {device_id : (device_ip, device_port)} pairs
        _ip:        IP address of this hub  (str)
        _port:      Port number this hub is listening on  (int)
    """

    _authenticated_devices = None
    _ip = None
    _port = None

    def __init__(self, name, ip, port):
        """
        Constructor: Instantiates a Hub instance.
        """
        super().__init__(id)

        # assign private properties
        self.name = name
        self._authenticated_devices = {}
        self._ip = ip
        self._port = int(port)
        self._buf = 1024 * 2

        self.init_sockets()

    def logAction(self, action)  #creating a new block to log action

    def send(self, message, recipient):
        """
        Sends an encrypted message to a recipient with UDP.
            message:    plaintext to be sent
            recipient:  (IP, port), retreived from _authenticated_devices
        """
        # encrypt the message
        cipher_text = self.encrypt(message).encode("utf-8")
        # send the packet over UDP
        self.commSocket.sendto(cipher_text, recipient)

        #Blockchain: sends record of action to other devices and hub so they can update their ledgers
        self.logAction(f'Sent message to {recipient}')
        super.send(message, recipient)

    def receive(self):
        """
        Listens for and decrypts an encrypted message.
        """        
        # Read header
        try :
            data, addr = self.commSocket.recvfrom(self._buf)
            data = self.decrypt(data.decode('utf-8'))
            data_type, message = data.split(':')
        except Exception as e:
            print(e)
            return "Error reading response", ("0.0.0.0", 1111)
        
        
        if data_type == "image":
            try:
                # Receive image
                data_length = int(message)
                TCP_socket = socket(AF_INET, SOCK_STREAM)
                TCP_socket.bind((self._ip, 8085))
                self.send("ack", addr)
                TCP_socket.listen(8085)
                
                ## Accpet incoming connection
                conn, client_tcp_addr = TCP_socket.accept()
                print("Recieved TCP connection from : " + client_tcp_addr[0])
    
                encrypted_data = b''
                expected_length = 0              
                
                while expected_length < data_length:             
                    data = conn.recv(data_length - len(encrypted_data))
                    if not data:
                        break
                    encrypted_data += data
                    
                self.send("done", addr)               
                conn.close()
                    
                plain_img = Image.open(io.BytesIO(encrypted_data))
                
                display_thread = threading.Thread(target=self.show_image, args=(plain_img,))
                display_thread.daemon = True  # Set as daemon thread
                display_thread.start()                
                return "Image Data recieved", addr
            
            
            except Exception as e:
                print(e)
                traceback.print_exc()
                return "Image Data error", ("0.0.0.0", 1111)
        
        else:   
            # receive the data
            print(f"Receiving message from {addr}")
            # decrypt the msg
            plain_text = message
            return plain_text, addr
        
        #Blockchain: takes in block from another device to update this device's ledger
        self.logAction("Received a message")
        return super().recieve()
    
    #fetches each device's blockchain state and checks their integrity
    def verifyLedgers(self) 
        
    #fetches device's blockchain state and checks a device's blockchain integrity
    def checkDeviceChain(self, device_id) 
        
        
    def show_image(self, image):
        image.show()

    def init_sockets(self):
        """
        Creates a socket. For initialization.
        """
        addr = (self._ip, self._port)

        UDP_socket = socket(AF_INET, SOCK_DGRAM)
        UDP_socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
        UDP_socket.bind(addr)

        self.setSocket(UDP_socket)
        return

    def register_device(self, device_id, device_ip, device_port):
        """
        Add the device to the internal list of authenticated devices.

        device_id:  id of the target IoT device
        deivce_ip:  IP address of the target IoT device
        """
        self._authenticated_devices[device_id] = (device_ip, device_port)

    def user_input_loop(self, hub):
        """
        Main loop that prompts users for commands.
            send:
        """
        while True:
            # main device loop
            # hub.receive()

            # _____for debugging uses only (input will be replaced by actual user device)_____
            user_input = input("Enter a debug command (send, register, list, exit): ")

            if user_input == "send":
                # sends a message to target device ID
                recipient_id = input("Enter recipient ID: ")
                message = input("Enter message: ")
                recipient_ip, recipient_port = hub._authenticated_devices[recipient_id]
                hub.send(message, (recipient_ip, int(recipient_port)))

            elif user_input == "send-m":
                # manual input for receipient addr
                recipient_ip = input("Enter recipient IP: ")
                recipient_port = input("Enter recipient port: ")
                message = input("Enter message to send: ")
                hub.send(message, (recipient_ip, int(recipient_port)))

            elif user_input == "register":
                # add device to authenticated list
                device_id = input("Enter device ID: ")
                device_ip = input("Enter device IP: ")
                device_port = input("Ender device port: ")
                hub.register_device(device_id, device_ip, device_port)
                print(f"--Device {device_id} registered with IP {device_ip}")

            elif user_input == "list":
                # list out all the authenticated devices
                print(hub._authenticated_devices)

            elif user_input == "key":
                # update key
                self.setEncryption(int(input("Key: ")), upperCaseAll=False)

            elif user_input == "exit":
                # exit the program
                print("HUB terminated")
                return

            else:
                print("Invalid command.")

            time.sleep(2)

    def receive_message(self, hub):
        """
        Second thread that continuously listens for messages.
        """
        while True:
            recv = hub.receive()
            print(recv)


def main():
    print("Setting up a new Hub..")
    input_ip = HUB_IP
    input_port = HUB_PORT
    hub = Hub("HUB", input_ip, input_port)

    hub.setEncryption(KEY, upperCaseAll=False, removeSpace=False)

    receive_thread = threading.Thread(target=hub.receive_message, args=(hub,))
    user_input_thread = threading.Thread(target=hub.user_input_loop, args=(hub,))

    receive_thread.start()
    user_input_thread.start()

    receive_thread.join()
    user_input_thread.join()


if __name__ == "__main__":
    main()
