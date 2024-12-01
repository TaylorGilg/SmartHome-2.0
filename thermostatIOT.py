import logging
from IOTdevice import IOTDevice
import random, time
from datetime import datetime
from data.config import *
import threading
from socket import *
import json

logging.basicConfig(
    filename='thermostat.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

class thermostatIOT(IOTDevice):

    def __init__(self, id, location="unknown"):
        super().__init__(id, "Thermostat", location)
        self.id = id
        self.location = location
        self._temperature = self.generate_random_temperature()
        self._fan_speed = self.map_fan_speed('med')
        self._state = "off"
        self._status = "off"
        self._time_thermostat = "00:00"
        logging.info(f"Thermostat {id} initialized at location: {location}")
        logging.info(f"Initial Temperature: {self._temperature}°F")

    SPEED_MAPPING = {'high': 0.5, 'med': 0.3, 'low': 0.1}

    @staticmethod
    def map_fan_speed(fan_speed):
        return thermostatIOT.SPEED_MAPPING.get(fan_speed, 0.5)

    def generate_random_temperature(self):
        return round(random.uniform(65, 75), 2)

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
            with socket(AF_INET, SOCK_STREAM) as tcp_socket:
                tcp_socket.connect(recipient)
                tcp_socket.sendall(message.encode("utf-8"))
                print(f"{self.device_type} {self.id} sent: {message} to {recipient}")
        except Exception as e:
            logging.error(f"Error in send for {self.device_type} {self.id}: {e}")
            raise

    def receive(self):
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
            print(f"{self.device_type} {self.id} received: {plain_text}")
            return plain_text, addr
        except Exception as e:
            logging.error(f"Error in receive for {self.device_type} {self.id}: {e}")
            raise

    def init_sockets(self, ip, port):
        try:
            self.setIP(ip)
            self.setPort(port)
            self.tcp_port = port + 1000
            self.commSocket = socket(AF_INET, SOCK_STREAM)
            self.commSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            self.commSocket.bind((self.ip, self.port))
            self.commSocket.listen(5)
            print(f"{self.device_type} {self.id} initialized TCP socket on {ip}:{self.tcp_port}")
        except Exception as e:
            logging.error(f"Error initializing socket for {self.device_type} {self.id}: {e}")
            raise

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
                    logging.error(f"Error handling TCP request from {addr}: {e}")
                finally:
                    conn.close()
        except Exception as e:
            logging.error(f"Error starting TCP server for {self.device_type} {self.id}: {e}")
            raise

    def process_command(self, command, message=None):
        try:
            if command == "error":
                return f"ERROR: {message}"
            mapper = {
                'get_status': self.get_status,
                'get_state': self.get_state,
                'get_temperature': self.get_temperature,
                'set_temperature': self.set_temperature,
                'set_heater': self.turn_on_heater,
                'set_ac': self.turn_on_ac,
                'turn_off': self.turn_off_thermostat,
                'get_location': self.get_location,
                'set_location': self.set_location,
                'get_blockchain_data': self.get_blockchain_data
            }

            if command not in mapper:
                logging.warning(f"Unknown command '{command}' received by Thermostat {self.id}")
                return f"ERROR: Unknown command '{command}'"

            result = mapper[command](message) if message else mapper[command]()

            # Log action and create a new block
            self.blockchain.new_interaction(sender=self.id, recipient="Hub", 
                                            data={"command": command, "message": message, "result": result})
            proof = self.blockchain.proof_of_work(self.blockchain.last_block['proof'])
            self.blockchain.new_block(proof)

            # Display the blockchain
            self.display_blockchain()

            logging.info(f"Command '{command}' executed successfully on Thermostat {self.id} with result: {result}")
            return str(result)

        except Exception as e:
            logging.error(f"Error executing command '{command}' on Thermostat {self.id}: {e}")
            return f"ERROR from {self.id}: {str(e)}"


# Main method to start thermostat IOT
def start_thermostat(therm_id, location, ip, port):
    try:
        thermostat = thermostatIOT(therm_id, location)
        thermostat.setEncryption(KEY, upperCaseAll=False, removeSpace=False)
        thermostat.init_sockets(ip, port)  # Initialize sockets first

        # Start TCP server on a separate thread for blockchain handling
        tcp_thread = threading.Thread(target=thermostat.start_TCP)
        tcp_thread.daemon = True  # Thread ends when the program exits
        tcp_thread.start()  # Start thread
        print(f"Thermostat {thermostat.id}: TCP server started for blockchain handling.")
        print(f"Setting up Thermostat {therm_id} at {location}")
        print(f"Thermostat {therm_id} listening on {ip}:{port}")

        while True:
            try:
                conn, addr = thermostat.commSocket.accept()  # TCP accept
                response = conn.recv(4096).decode("utf-8")
                if response == "exit":
                    break
                    
                logging.info(f"Thermostat {therm_id}: received: {response}")
                print(f"Thermostat {therm_id} received: {response}")
                command, message = thermostat.parse_command(response)
                output = thermostat.process_command(command, message)
                
                logging.info(f"Thermostat {therm_id}: Sending response: {output}")
                print(f"Thermostat {therm_id} sending response: {output}")
                conn.sendall(output.encode("utf-8"))
                conn.close()
                
            except Exception as e:
                error_msg = f"Error in Thermostat {therm_id}: {str(e)}"
                print(error_msg)

        print(f"Thermostat {therm_id} shutting down...")

    except Exception as e:
        print(f"Fatal error in Thermostat {therm_id}: {str(e)}")


# Entry point for running the thermostat IOT
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python thermostatIOT.py <therm_id> <location> <port>")
        print("Example: python thermostatIOT.py therm1 'Living Room' 8087")
        sys.exit(1)

    therm_id = sys.argv[1]
    location = sys.argv[2]
    port = int(sys.argv[3])

    logging.info(f"Starting Thermostat with ID: {therm_id}, Location: {location}, Port: {port}")
    start_thermostat(therm_id, location, THERMOSTAT_IP, port)
