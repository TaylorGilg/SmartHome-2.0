from IOTdevice import IOTDevice
from data.config import *
import time

class DoorLock(IOTDevice):
    def __init__(self, id):
        super().__init__(id)
        self._state = "off"
        self._status = "unlocked"
        self._code = "0000"
        self._lock_time = "00:00"
        print(f"DoorLock initialized with ID: {id}")
    
    def process_command(self, command, message=None):
        try:
            print(f"Processing command: {command} with message: {message}")
            
            if command == "error":
                return f"ERROR: {message}"
            
            mapper = {
                'set_state': self.set_state,
                'set_status': self.set_status,
                'set_keyless_entry': self.set_keyless_entry,
                'set_lock_time': self.set_lock_time,
                'get_state': self.get_state,
                'get_status': self.get_status,
                'get_keyless_entry': self.get_keyless_entry,
                'get_lock_time': self.get_lock_time,
            }
            
            if command not in mapper:
                return f"ERROR: Unknown command '{command}'"
                
            result = mapper[command](message) if message else mapper[command]()
            print(f"Command result: {result}")
            return str(result)
            
        except Exception as e:
            print(f"Error in process_command: {str(e)}")
            return f"ERROR: {str(e)}"

def main():
    try:
        lock = DoorLock("doorlock1")
        lock.setEncryption(KEY, upperCaseAll=False, removeSpace=False)    
        
        print("Setting up a new Smart DoorLock..")
        lock.init_sockets(DOORLOCK_IP, DOORLOCK_PORT)
        print(f"DoorLock listening on {DOORLOCK_IP}:{DOORLOCK_PORT}")

        while True:
            try:
                print("\nWaiting for command...")
                response, addr = lock.receive()
                print(f"Received raw message: {response}")
                
                if response == "exit":
                    break
                
                command, message = lock.parse_command(response)
                print(f"Parsed command: {command}, message: {message}")
                
                output = lock.process_command(command, message)
                print(f"Sending response: {output}")
                
                lock.send(output, (HUB_IP, HUB_PORT))
                
            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                print(error_msg)
                try:
                    lock.send(error_msg, (HUB_IP, HUB_PORT))
                except:
                    print("Failed to send error message to hub")
        
        print("DoorLock shutting down...")
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")

if __name__ == '__main__': 
    main()