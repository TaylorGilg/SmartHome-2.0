
from IOTdevice import IOTDevice
from data.config import *
import time

class DoorLock(IOTDevice):
    def __init__(self, id, location="unknown"):
        super().__init__(id)
        self._state = "off"
        self._status = "unlocked"
        self._code = "0000"
        self._lock_time = "00:00"
        self.location = location
        print(f"DoorLock {id} initialized at location: {location}")
    
    def set_state(self, state):
        try:
            if state == "on" or state == "off":    
                self._state = state
                return f"DoorLock {self.id}: State set to {state}"
            else:
                raise Exception("invalid message", state)
        except Exception as e:
            raise e

    def set_status(self, status):
        try:
            if self._state == "off": 
                raise Exception("off")
            if status == "lock" or status == "unlock":
                self._status = status + "ed"
                return f"DoorLock {self.id}: Status set to {self._status}"
            else:
                raise Exception("invalid message", status)
        except Exception as e:
            raise e
    
    def set_keyless_entry(self, code):
        try:
            if self._state == "off": 
                raise Exception("off")
            if len(code) == 4 and code.isdigit():
                self._code = code
                return f"DoorLock {self.id}: Keyless entry code updated"
            else:
                raise Exception("invalid message", code)
        except Exception as e:
            raise e
    
    def set_lock_time(self, lock_time):
        try:
            if self._state == "off": 
                raise Exception("off")
            hours = lock_time[:2]
            minutes = lock_time[3:]
            if hours.isdigit() and minutes.isdigit() and int(hours) >= 0 and int(hours) <= 23 \
                and int(minutes) >= 0  and int(minutes) <= 59 and len(lock_time) == 5 and lock_time[2] == ":": 
                    self._lock_time = lock_time
                    return f"DoorLock {self.id}: Lock time set to {lock_time}"
            else:
                raise Exception("invalid message", lock_time)
        except Exception as e:
            raise e
    
    def get_state(self):
        return f"DoorLock {self.id}: {self._state}"
    
    def get_status(self):
        if self._state == "off": 
            raise Exception("off")
        return f"DoorLock {self.id}: {self._status}"
    
    def get_keyless_entry(self):
        if self._state == "off": 
            raise Exception("off")
        return f"DoorLock {self.id}: Code is {self._code}"
        
    def get_lock_time(self):
        if self._state == "off": 
            raise Exception("off")
        return f"DoorLock {self.id}: Lock time is {self._lock_time}"
    
    def get_location(self):
        return f"DoorLock {self.id} location: {self.location}"
    
    def set_location(self, new_location):
        self.location = new_location
        return f"DoorLock {self.id} location set to {new_location}"
    
    # Searches for received message from Hub and calls it's corresponding function
    def process_command(self, command, message=None):
        try:
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
                'get_location': self.get_location,
                'set_location': self.set_location
            }
            return mapper[command](message) if message else mapper[command]()
        
            if command not in mapper:
                return f"ERROR: Unknown command '{command}'"
                
            result = mapper[command](message) if message else mapper[command]()
            print(f"Command result for {self.id}: {result}")
            return str(result)
            
        except Exception as e:
            return f"ERROR from {self.id}: {str(e)}"
            

def start_doorlock(lock_id, location, ip, port):
    try:
        lock = DoorLock(lock_id, location)
        lock.setEncryption(KEY, upperCaseAll=False, removeSpace=False)    
        print(f"Setting up DoorLock {lock_id} at {location}")
        lock.init_sockets(ip, port)
        print(f"DoorLock {lock_id} listening on {ip}:{port}")
        while True:
            try:
                response, addr = lock.receive()
                if response == "exit":
                    break
                    
                print(f"DoorLock {lock_id} received: {response}")
                command, message = lock.parse_command(response)
                output = lock.process_command(command, message)
                
                print(f"DoorLock {lock_id} sending response: {output}")
                lock.send(output, (HUB_IP, HUB_PORT))
                
            except Exception as e:
                error_msg = f"Error in DoorLock {lock_id}: {str(e)}"
                print(error_msg)
                lock.send(error_msg, (HUB_IP, HUB_PORT))

            print(f"DoorLock {lock_id} shutting down...")

    except Exception as e:
            print(f"Fatal error in DoorLock {lock_id}: {str(e)}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python doorlockIOT.py <lock_id> <location> <port>")
        print("Example: python doorlockIOT.py door1 'Front Door' 8084")
        sys.exit(1)
        
    lock_id = sys.argv[1]
    location = sys.argv[2]
    port = int(sys.argv[3])

    start_doorlock(lock_id, location, DOORLOCK_IP, port)