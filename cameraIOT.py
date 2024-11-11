from IOTdevice import IOTDevice
from Vigenere import VigenereCipher
from data.config import *
import time

class CameraIOT(IOTDevice):
    """Simulate camera IOT"""
    status = None
    
    def __init__(self, id):
        super().__init__(id)
        self.status = "live"
    
    
    def process_command(self, command, message=None):
        """_summary_

        Args:
            command (string): Funtion to execute
            message (string, optional): argument for the function. Defaults to None.

        Returns:
            string: result of the function call
        """
        mapper = {
        'get_status': self.get_status,
        'set_status': self.set_status
        }
           
        return mapper[command](message) if message else mapper[command]()
           
            
    def get_status(self):
        return self.status
    
    def set_status(self, state):
        self.status = state
        return "200"
    
    
if __name__ == "__main__":
    camera1 = CameraIOT("c12")
    camera1.setEncryption(KEY, upperCaseAll=False, removeSpace=False)

    print("Setting up a new Smart Camera..")
    input_ip = CAMERA_IP
    input_port = CAMERA_PORT
    camera1.init_sockets(input_ip, input_port)
    
    print("Recieving......")
    response = camera1.receive()
    command, message = camera1.parse_command(response) 
    
    while command != "exit": 

        output = camera1.process_command(command, message)  
        
        print("Repsonse sent to ")        
        camera1.send(output, (HUB_IP, HUB_PORT))
        print("Recieving......")
        response = camera1.receive()
        command, message = camera1.parse_command(response)
        
    print("IOT has exited")
    
    