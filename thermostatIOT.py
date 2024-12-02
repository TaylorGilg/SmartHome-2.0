import logging
from IOTdevice import IOTDevice
import random, time
from datetime import datetime
from data.config import *
import threading


logging.basicConfig(
    filename='thermostat.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# IoT Thermostat device with blockchain logging and dual TCP servers.
class thermostatIOT(IOTDevice):

    # Initialize the thermostat with blockchain capabilities.
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

    def get_temperature(self):
        return f"Thermostat {self.id}: {str(self._temperature)}°F"
    
    SPEED_MAPPING = {'high': 0.5, 'med': 0.3, 'low': 0.1}
    
    @staticmethod
    def map_fan_speed(fan_speed):
        return thermostatIOT.SPEED_MAPPING.get(fan_speed, 0.5)
    
    def get_state(self):
        return f"Thermostat {self.id}: {self._state}"
    
    def get_status(self):
        return f"Thermostat {self.id}: {self._status}"
    
    def get_location(self):
        return f"Thermostat {self.id} location: {self.location}"
    
    def set_location(self, new_location):
        self.location = new_location
        return f"Thermostat {self.id} location set to {new_location}"
    
    def set_state(self, state):
        try:
            if state in ["on", "off"]:
                self._state = state
                logging.info(f"Thermostat {self.id}: State set to {state}")
                return f"Thermostat {self.id}: State set to {state}"
            else:
                raise Exception("Invalid message", state)
        except Exception as e:
            logging.error(f"Error setting state: {e}")
            raise e
    
    def set_status(self, status):
        try:
            if self._state == "off":
                raise Exception("off")
            if status in ["Heating", "Cooling", "on"]:
                self._status = status
                return f"Thermostat {self.id}: Status set to {status}"
            else:
                raise Exception("Invalid message", status)
        except Exception as e:
            raise e

    def turn_on_heater(self):
        try:
            self.set_state("on")
            self.set_status("Heating")
            return self.generate_sensor_data()
        except Exception as e:
            return f"ERROR in {self.id}: {str(e)}"
        
    def turn_on_ac(self):
        try:
            self.set_state("on")
            self.set_status("Cooling")
            return self.generate_sensor_data()
        except Exception as e:
            return f"ERROR in {self.id}: {str(e)}"
        
    def turn_off_thermostat(self):
        try:
            self.set_state("off")
            self.set_status("off")
            return self.generate_sensor_data()
        except Exception as e:
            return f"ERROR in {self.id}: {str(e)}"
    
    def set_temperature(self, message):
        try:
            # Split the input message to extract temperature and fan speed
            message = message.split(",")
            new_temperature = float(message[0])
            fan_speed = message[1]
            update_interval = 1

            # Log the received command details
            logging.info(f"Thermostat {self.id}: Received set_temperature command. Target: {new_temperature}°F, Fan Speed: {fan_speed}")

            if fan_speed is not None:
                self._fan_speed = self.map_fan_speed(fan_speed)
                current_time = time.time()

                # Gradually adjust the temperature until it reaches the desired range
                while not (new_temperature - 0.5 <= self._temperature <= new_temperature + 0.5):
                    if self._temperature > new_temperature:
                        self.set_state("on")
                        self.set_status("Cooling")
                        self._temperature -= self._fan_speed
                    elif self._temperature < new_temperature:
                        self.set_state("on")
                        self.set_status("Heating")
                        self._temperature += self._fan_speed

                    current_time += update_interval
                    readable_time = datetime.fromtimestamp(current_time).strftime('%H:%M:%S')
                    logging.info(f"Thermostat {self.id}: Adjusting Temperature: {round(self._temperature, 2)}°F | Time: {readable_time}")
                    time.sleep(update_interval)

            # Log the successful adjustment
            result = f"Thermostat {self.id}: Reached {str(round(self._temperature, 2))}°F"
            logging.info(result)
            return result

        except Exception as e:
            # Log the error and return the error message
            error_msg = f"ERROR in {self.id}: {str(e)}"
            logging.error(error_msg)
            return error_msg
            
    def generate_random_temperature(self):
        return round(random.uniform(65, 75), 2)
                
    def generate_sensor_data(self):
        try:
            self._fan_speed = self.map_fan_speed('med')
            current_time = time.time()
            readable_time = datetime.fromtimestamp(current_time).strftime('%H-%M-%S')
            
            if self.get_state() == "on":
                if self._status == "Heating":
                    self._temperature += self._fan_speed
                if self._status == "Cooling":
                    self._temperature -= self._fan_speed
                    
                print(f"Thermostat {self.id}: Temperature: {round(self._temperature, 2)}°F | Time: {readable_time}")
                
            return f"Thermostat {self.id}: Temperature: {round(self._temperature, 2)}°F at {readable_time}"
        except Exception as e:
            return f"ERROR in {self.id}: {str(e)}"
            
    # Process commands received via TCP and log them to blockchain. Each command creates a new block in our chain for integrity.
    def process_command(self, command, message=None):
        try:
            # Split command and MAC
            if "|" in command:
                command, _ = command.rsplit("|", 1) # Discard the MAC

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

            # Critical blockchain component: Log this command as a new interaction
            self.blockchain.new_interaction(sender = self.id, recipient = "Hub", 
            data = {"command": command, "message": message, "result": result})
            # Create new block with proof of work
            proof = self.blockchain.proof_of_work(self.blockchain.last_block['proof'])
            self.blockchain.new_block(proof)

            #display the blockchain
            self.display_blockchain()

            logging.info(f"Command '{command}' executed successfully on Thermostat {self.id} with result: {result}")
            return str(result)

        except Exception as e:
            logging.error(f"Error executing command '{command}' on Thermostat {self.id}: {e}")
            return f"ERROR from {self.id}: {str(e)}"

# Initialize and start thermostat with dual TCP servers
# 1. Main port: Handles encrypted device commands
# 2. Port+1000: Dedicated to blockchain consensus protocol
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
                # Use parent's receive method for encryption
                message, addr = thermostat.receive()
                    
                if message == "exit":
                    break
                
                # Separate the MAC from the command
                if "|" in response:
                    response, _ = response.rsplit("|", 1) # Discard the MAC
                    print(f"Thermostat {therm_id} parsed command: {response.strip()}")

                logging.info(f"Thermostat {therm_id}: received: {response}")
                print(f"Thermostat {therm_id} received: {response}")

                # Parse and process the command
                command, message = thermostat.parse_command(response)
                output = thermostat.process_command(command, message)
                
                command, msg = thermostat.parse_command(message)
                output = thermostat.process_command(command, msg)
                
                # Use parent's send method for encryption
                logging.info(f"Thermostat {therm_id}: Sending response: {output}")
                print(f"Thermostat {therm_id} sending response: {output}")
                thermostat.send(output, addr)
                
            except Exception as e:
                error_msg = f"Error in Thermostat {therm_id}: {str(e)}"
                logging.error(error_msg)
                print(error_msg)
                try:
                    # Send encrypted error message
                    thermostat.send(error_msg, addr)
                except:
                    pass

        print(f"Thermostat {therm_id} shutting down...")

    except Exception as e:
        print(f"Fatal error in Thermostat {therm_id}: {str(e)}")

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