from IOTdevice import IOTDevice
import random, time
from datetime import datetime
from data.config import *

class thermostatIOT(IOTDevice):
    """
    A Thermostat class for managing and communicating a temperature (in a smarthome).
    """
    def __init__(self, id):
        super().__init__(id)
        self.id = id
        self._temperature = self.generate_random_temperature()
        self._fan_speed = self.map_fan_speed('med')
        self._state = "off"
        self._status = "off"
        self._time_thermostate = "00:00"
    
    def get_temperature(self):
        return str(self._temperature)
    
    SPEED_MAPPING = {'high': .5, 'med': 0.3, 'low': 0.1}
    
    @staticmethod
    def map_fan_speed(fan_speed):
        return thermostatIOT.SPEED_MAPPING.get(fan_speed, 0.5)
    
    def get_state(self):
        return self._state
    
    def get_status(self):
        return self._status
    
    def set_state(self, state):
        if state == "on" or state == "off":    
            self._state = state
            return "200"
        else:
            raise Exception("invalid message", state)
    
    def set_status(self, status):
        if self._state == "off": 
                raise Exception("off")
        if status == "Heating" or status == "Cooling" or status == 'on':
            self._status = status
            return "200"
        else:
            raise Exception("invalid message", status)
    
    def turn_on_heater(self):
        try:
            self.set_state("on")
            self.set_status("Heating")
            return self.generate_sensor_data()
        except Exception as e:
            return f"ERROR: {str(e)}"
        
    def turn_on_ac(self):
        try:
            self.set_state("on")
            self.set_status("Cooling")
            return self.generate_sensor_data()
        except Exception as e:
            return f"ERROR: {str(e)}"
        
    def turn_off_thermostat(self):
        try:
            self.set_state("off")
            self.set_status("off")
            return self.generate_sensor_data()
        except Exception as e:
            return f"ERROR: {str(e)}"
    
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
                    print(f"Current Temperature: {round(self._temperature, 2)} °F | Timestamp: {readable_time}")
                    time.sleep(update_interval)
            
            return str(f"Reached {str(round(self._temperature, 2))} °F at {readable_time}")
        except Exception as e:
            return f"ERROR: {str(e)}"
            
    def generate_random_temperature(self):
        return round(random.uniform(65, 75), 2)
                
    def generate_sensor_data(self):
        try:
            self._fan_speed = self.map_fan_speed('med')
            current_time = time.time()
            readable_time = datetime.fromtimestamp(current_time).strftime('%H-%M-%S')
            update_interval = 1
            
            # Only run one iteration instead of continuous loop
            if self.get_state() == "on":
                if self._status == "Heating":
                    self._temperature += self._fan_speed
                if self._status == "Cooling":
                    self._temperature -= self._fan_speed
                    
                print(f"Temperature: {round(self._temperature, 2)} °F | Timestamp: {readable_time}")
                
            return str(f"Temperature: {round(self._temperature, 2)} °F | Timestamp: {readable_time}")
        except Exception as e:
            return f"ERROR: {str(e)}"
            
    def process_command(self, command, message=None):
        try:
            mapper = {
                'get_status': self.get_status,
                'get_state' : self.get_state,
                'get_temperature': self.get_temperature,
                'set_temperature': self.set_temperature,
                'set_heater': self.turn_on_heater,
                'set_ac': self.turn_on_ac,
                'turn_off': self.turn_off_thermostat,
            }
            return mapper[command](message) if message else mapper[command]()
        
        except TypeError as e:
            return f"ERROR: {e}"
        except Exception as e:
            exception = e.args[0]
            if exception == "off":
                return "ERROR: device currently off"
            elif exception == "invalid message":
                return f"ERROR: '{e.args[1]}' message not valid"
            else:
                return f"ERROR: {e} command not defined"
            
def main():
    try:
        thermostat = thermostatIOT("therm1")
        thermostat.setEncryption(KEY, upperCaseAll=False, removeSpace=False)
        
        print("Setting up a new Smart Thermostat..")
        thermostat.init_sockets(THERMOSTAT_IP, THERMOSTAT_PORT)
        
        print(f"Initial Temperature: {thermostat.get_temperature()} °F")
        print(f"Thermostat listening on {THERMOSTAT_IP}:{THERMOSTAT_PORT}")
        
        while True:
            try:
                print("\nWaiting for command...")
                response, addr = thermostat.receive()
                print(f"Received raw message: {response}")
                
                if response == "exit":
                    break
                    
                command, message = thermostat.parse_command(response)
                print(f"Parsed command: {command}, message: {message}")
                
                if command == "error":
                    output = f"Error: {message}"
                else:
                    output = thermostat.process_command(command, message)
                    
                print(f"Sending response: {output}")
                thermostat.send(output, (HUB_IP, HUB_PORT))
                
            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                print(error_msg)
                try:
                    thermostat.send(error_msg, (HUB_IP, HUB_PORT))
                except:
                    print("Failed to send error message to hub")
        
        print("Thermostat shutting down...")
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")

if __name__ == "__main__":
    main()