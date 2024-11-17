from IOTdevice import IOTDevice
from data.config import *
import time

class CameraIOT(IOTDevice):
    """Simulate camera IOT with support for multiple instances.
        Each camera can be identified by a unique ID (e.g., 'cam1', 'cam2', 'outdoor_cam', etc.)
    """
    def __init__(self, id, location="unknown"):
        super().__init__(id)
        self.status = "live"
        self.location = location
        print(f"Camera {id} initialized at location: {location}")
    
    
    def process_command(self, command, message=None):
        """Process received command"""
        try:
            if command == "error":
                return f"ERROR: {message}"
                
            mapper = {
                'get_status': self.get_status,
                'set_status': self.set_status,
                'get_location': self.get_location,
                'set_location': self.set_location,
                'get_blockchain_data': self.get_blockchain_data
            }
               
            return mapper[command](message) if message else mapper[command]()
        except KeyError:
            return f"ERROR: Unknown command '{command}'"
        except Exception as e:
            return f"ERROR: {str(e)}"
            
    def get_status(self):
        return f"Camera {self.id} status: {self.status}"
    
    def set_status(self, state):
        self.status = state
        return f"Camera {self.id} set to {state}"
    
    def get_location(self):
        return f"Camera {self.id} location: {self.location}"
    
    def set_location(self, new_location):
        self.location = new_location
        return f"Camera {self.id} location set to {new_location}"

    # Example of running multiple cameras
    def start_camera(camera_id, location, ip, port):
        try:
            camera = CameraIOT(camera_id, location)
            camera.setEncryption(KEY, upperCaseAll=False, removeSpace=False)

            print(f"Setting up Camera {camera_id} at {location}")
            camera.init_sockets(ip, port)

            print(f"Camera {camera_id} listening on {ip}:{port}")
            
            while True:
                try:
                    response, addr = camera.receive()
                    if response == "exit":
                        break
                        
                    print(f"Camera {camera_id} received: {response}")
                    command, message = camera.parse_command(response)
                    output = camera.process_command(command, message)
                    
                    print(f"Camera {camera_id} sending response: {output}")
                    camera.send(output, (HUB_IP, HUB_PORT))
                    
                except Exception as e:
                    error_msg = f"Error in camera {camera_id}: {str(e)}"
                    print(error_msg)
                    camera.send(error_msg, (HUB_IP, HUB_PORT))
            
                    print(f"Camera {camera_id} shutting down...")
        
        except Exception as e:
            print(f"Fatal error in camera {camera_id}: {str(e)}")

    if __name__ == "__main__":
        
    # Example of how to start different cameras:
        import sys
    
    if len(sys.argv) < 4:
        print("Usage: python cameraIOT.py <camera_id> <location> <port>")
        print("Example: python cameraIOT.py cam1 'Front Door' 8081")
        sys.exit(1)
            
        camera_id = sys.argv[1]
        location = sys.argv[2]
        port = int(sys.argv[3])
        start_camera(camera_id, location, CAMERA_IP, port)
        
    