import logging
from IOTdevice import IOTDevice
from data.config import *
import time
import threading
from socket import *

logging.basicConfig(
    filename='doorlock.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# DoorLock IoT device that extends IOTDevice.
# Implements secure door lock functionality with
# TCP command communication
# Blockchain logging for tamper-proof operation history
# Separate TCP server for blockchain consensus
class DoorLock(IOTDevice):
    def __init__(self, id, location="unknown"):
        super().__init__(id, "DoorLock", location)
        self._state = "off"
        self._status = "unlocked"
        self._code = "0000"
        self._lock_time = "00:00"
        self.location = location
        logging.info(f"DoorLock {id} initialized at location: {location}")

    def set_state(self, state):
        try:
            if state in ["on", "off"]:
                self._state = state
                logging.info(f"DoorLock {self.id}: State set to {state}")
                return f"DoorLock {self.id}: State set to {state}"
            else:
                raise ValueError("Invalid state")
        except Exception as e:
            logging.error(f"Error setting state: {e}")
            raise

    def set_status(self, status):
        try:
            if self._state == "off":
                raise RuntimeError("Cannot set status while device is off")
            if status in ["lock", "unlock"]:
                self._status = status + "ed"
                logging.info(f"DoorLock {self.id}: Status set to {self._status}")
                return f"DoorLock {self.id}: Status set to {self._status}"
            else:
                raise ValueError("Invalid status")
        except Exception as e:
            logging.error(f"Error setting status: {e}")
            raise

    def set_keyless_entry(self, code):
        try:
            if self._state == "off":
                raise RuntimeError("Cannot set keyless entry while device is off")
            if len(code) == 4 and code.isdigit():
                self._code = code
                logging.info(f"DoorLock {self.id}: Keyless entry code updated")
                return f"DoorLock {self.id}: Keyless entry code updated"
            else:
                raise ValueError("Invalid code format")
        except Exception as e:
            logging.error(f"Error setting keyless entry: {e}")
            raise

    def set_lock_time(self, lock_time):
        try:
            if self._state == "off":
                raise RuntimeError("Cannot set lock time while device is off")
            hours, minutes = lock_time.split(":")
            if hours.isdigit() and minutes.isdigit() and 0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59:
                self._lock_time = lock_time
                logging.info(f"DoorLock {self.id}: Lock time set to {lock_time}")
                return f"DoorLock {self.id}: Lock time set to {lock_time}"
            else:
                raise ValueError("Invalid time format")
        except Exception as e:
            logging.error(f"Error setting lock time: {e}")
            raise

    def get_state(self):
        return f"DoorLock {self.id}: {self._state}"

    def get_status(self):
        if self._state == "off":
            raise RuntimeError("Device is off")
        return f"DoorLock {self.id}: {self._status}"

    def get_keyless_entry(self):
        if self._state == "off":
            raise RuntimeError("Device is off")
        return f"DoorLock {self.id}: Code is {self._code}"

    def get_lock_time(self):
        if self._state == "off":
            raise RuntimeError("Device is off")
        return f"DoorLock {self.id}: Lock time is {self._lock_time}"

    def get_location(self):
        return f"DoorLock {self.id} location: {self.location}"

    def set_location(self, new_location):
        self.location = new_location
        logging.info(f"DoorLock {self.id}: Location updated to {new_location}")
        return f"DoorLock {self.id} location set to {new_location}"

    # Process received commands and log them to blockchain where each command interaction creates a new block for chaining.
    def process_command(self, command, message=None):
        try:
            # Split command and MAC
            if "|" in command:
                command, _ = command.rsplit("|", 1) # Discard the MAC

            mapper = {
                'set_state': self.set_state,
                'set_status': self.set_status,
                'set_keyless_entry': self.set_keyless_entry,
                'set_lock_time': self.set_lock_time,
                'get_state': self.get_state,
                'get_status': self.get_status,
                'get_keyless_entry': self.get_keyless_entry,
                'get_lock_time': self.get_lock_time,
                'get_location': self.get_location,
                'set_location': self.set_location,
                'get_blockchain_data': self.get_blockchain_data
            }

            if command not in mapper:
                logging.warning(f"Unknown command '{command}' received by DoorLock {self.id}")
                return f"ERROR: Unknown command '{command}'"

            result = mapper[command](message) if message else mapper[command]()

            #log action and create a new block
            self.blockchain.new_interaction(sender = self.id, recipient = "Hub", 
            data = {"command": command, "message": message, "result": result})
            proof = self.blockchain.proof_of_work(self.blockchain.last_block['proof'])
            self.blockchain.new_block(proof)


            logging.info(f"Command '{command}' executed successfully on Thermostat {self.id} with result: {result}")
            return str(result)
        
        except Exception as e:
            logging.error(f"Error executing command '{command}': {e}")
            return f"ERROR from {self.id}: {e}"

# Initialize and start doorlock device with dual TCP servers
# 1. Main port: Handles encrypted device commands
# 2. Port+1000: Dedicated to blockchain consensus protocol
def start_doorlock(lock_id, location, ip, port):
    try:
        lock = DoorLock(lock_id, location)
        lock.setEncryption(KEY, upperCaseAll=False, removeSpace=False)
        lock.init_sockets(ip, port)

        # Start blockchain consensus server in separate thread
        tcp_thread = threading.Thread(target=lock.start_TCP)
        tcp_thread.daemon = True
        tcp_thread.start()
        logging.info(f"Doorlock {lock.id}: TCP server started for blockchain handling.")
        print(f"DoorLock {lock_id} running at {location} ({ip}:{port})")

        while True:
            try:
                # Use Communicator's receive method instead of direct socket
                message, addr = lock.receive()
                
                if message == "exit":
                    break

                # Separate the MAC from the command
                if "|" in response:
                    response, _ = response.rsplit("|", 1) # Discard the MAC
                    print(f"Thermostat {lock_id} parsed command: {response.strip()}")
                
                print(f"Doorlock {lock_id} received: {response}")

                # Parse and process the command
                command, message = lock.parse_command(response)
                output = lock.process_command(command, message)
                # Use Communicator's send method instead of direct socket
                lock.send(output, addr)
            except Exception as e:
                error_msg = f"Error in DoorLock {lock_id}: {str(e)}"
                print(error_msg)
                # Use Communicator's send for error messages too
                lock.send(error_msg, addr)
    except Exception as e:
        logging.critical(f"Fatal error in DoorLock {lock_id}: {e}")
    finally:
        logging.info(f"DoorLock {lock_id} shutting down...")

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 4:
        print("Usage: python doorlockIOT.py <lock_id> <location> <port>")
        sys.exit(1)

    lock_id = sys.argv[1]
    location = sys.argv[2]
    port = int(sys.argv[3])

    start_doorlock(lock_id, location, DOORLOCK_IP, port)