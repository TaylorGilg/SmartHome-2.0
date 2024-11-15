from IOTdevice import IOTDevice
import random, time
from datetime import datetime
from data.config import *

class thermostatIOT(IOTDevice):

    def __init__(self, id, location="unknown"):
        super().__init__(id)
        self.id = id
        self.location = location
        self._temperature = self.generate_random_temperature()
        self._fan_speed = self.map_fan_speed('med')
        self._state = "off"
        self._status = "off" 
        self._time_thermostate = "00:00"
        print(f"Thermostat {id} initialized at location: {location}")
        print(f"Initial Temperature: {self._temperature}°F")
    
    def get_temperature(self):
        return f"Thermostat {self.id}: {str(self._temperature)}°F"
    
    #Possible fan_speeds
    SPEED_MAPPING = {'high': .5, 'med': 0.3, 'low': 0.1}
    
    @staticmethod  # Static method doesn't need 'self'
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
            if state == "on" or state == "off":    
                self._state = state
                return f"Thermostat {self.id}: State set to {state}"
            else:
                raise Exception("invalid message", state)
        except Exception as e:
            raise e
    
    def set_status(self, status):
        try:
            if self._state == "off": 
                raise Exception("off")
            if status == "Heating" or status == "Cooling" or status == 'on':
                self._status = status
                return f"Thermostat {self.id}: Status set to {status}"
            else:
                raise Exception("invalid message", status)
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
            message = message.split(",")
            new_temperature = float(message[0])
            fan_speed = message[1]
            update_interval = 1
            
            if fan_speed is not None:
                self._fan_speed = self.map_fan_speed(fan_speed)
                current_time = time.time()
                readable_time = datetime.fromtimestamp(current_time).strftime('%H-%M-%S')
                
                while not (new_temperature - 0.5 <= self._temperature <= new_temperature + 0.5):
                    if(self._temperature > new_temperature):
                        self.set_state("on")
                        self.set_status("Cooling")
                        self._temperature -= self._fan_speed
                        
                    elif(self._temperature < new_temperature):
                        self.set_state("on")
                        self.set_status("Heating")
                        self._temperature += self._fan_speed
                        
                    current_time += update_interval
                    print(f"Thermostat {self.id}: Current Temperature: {round(self._temperature, 2)}°F | Time: {readable_time}")
                    time.sleep(update_interval)
                return f"Thermostat {self.id}: Reached {str(round(self._temperature, 2))}°F at {readable_time}"
        except Exception as e:
            return f"ERROR in {self.id}: {str(e)}"
    
    def generate_random_temperature(self):
        return round(random.uniform(65, 75), 2)
    # Generate a random temperature between 65 and 75 in Fahrenheit  
                
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
            
    # Searches for received message from Hub and calls it's corresponding function
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
            }
            
            if command not in mapper:
                return f"ERROR: Unknown command '{command}'"
                
            result = mapper[command](message) if message else mapper[command]()
            print(f"Command result for {self.id}: {result}")
            return str(result)
            
        except Exception as e:
            return f"ERROR from {self.id}: {str(e)}"

def start_thermostat(therm_id, location, ip, port):
    try:
        thermostat = thermostatIOT(therm_id, location)
        thermostat.setEncryption(KEY, upperCaseAll=False, removeSpace=False)
        
        print(f"Setting up Thermostat {therm_id} at {location}")
        thermostat.init_sockets(ip, port)
        print(f"Thermostat {therm_id} listening on {ip}:{port}")
        while True:
            try:
                response, addr = thermostat.receive()
                if response == "exit":
                    break
                    
                print(f"Thermostat {therm_id} received: {response}")
                command, message = thermostat.parse_command(response)
                output = thermostat.process_command(command, message)
                
                print(f"Thermostat {therm_id} sending response: {output}")
                thermostat.send(output, (HUB_IP, HUB_PORT))
                
            except Exception as e:
                error_msg = f"Error in Thermostat {therm_id}: {str(e)}"
                print(error_msg)
                thermostat.send(error_msg, (HUB_IP, HUB_PORT))
        
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

    start_thermostat(therm_id, location, THERMOSTAT_IP, port)
    