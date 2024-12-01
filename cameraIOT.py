import logging
from IOTdevice import IOTDevice
from data.config import *
import time
import threading

logging.basicConfig(
    filename='camera.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

class CameraIOT(IOTDevice):
    """Simulate camera IOT with support for multiple instances.
        Each camera can be identified by a unique ID (e.g., 'cam1', 'cam2', 'outdoor_cam', etc.)
    """
    def __init__(self, id, location="unknown"):
        super().__init__(id, "Camera", location)
        self.status = "live"
        self.location = location
        logging.info(f"Camera {id} initialized at location: {location}")
    
    def process_command(self, command, message=None):
        """Process received command"""
        try:
            logging.info(f"Camera {self.id}: Processing command '{command}' with message: '{message}'")
            mapper = {
                'get_status': self.get_status,
                'set_status': self.set_status,
                'get_location': self.get_location,
                'set_location': self.set_location,
                'get_blockchain_data': self.get_blockchain_data
            }
            if command not in mapper:
                logging.warning(f"Camera {self.id}: Unknown command '{command}'")
                return f"ERROR: Unknown command '{command}'"

            result = mapper[command](message) if message else mapper[command]()

            # Critical blockchain component: Log this command as a new interaction
            self.blockchain.new_interaction(sender = self.id, recipient = "Hub", 
            data = {"command": command, "message": message, "result": result})
            
            # Create new block with proof of work for tamper resistance
            proof = self.blockchain.proof_of_work(self.blockchain.last_block['proof'])
            self.blockchain.new_block(proof)

            # Write updated blockchain to file for monitoring
            self.display_blockchain()

            logging.info(f"Camera {self.id}: Command '{command}' executed successfully with result: '{result}'")
            return result
        except Exception as e:
            logging.error(f"Camera {self.id}: Error processing command '{command}': {e}")
            return f"ERROR: {str(e)}"
            
    def get_status(self):
        return f"Camera {self.id} status: {self.status}"
    
    def set_status(self, state):
        try:
            self.status = state
            logging.info(f"Camera {self.id} status set to {state}")
            return f"Camera {self.id} set to {state}"
        except Exception as e:
            logging.error(f"Error setting status: {e}")
            raise e
    
    def get_location(self):
        logging.info(f"Camera {self.id}: Retrieved location: {self.location}")
        return f"Camera {self.id} location: {self.location}"
    
    def set_location(self, new_location):
        try:
            old_location = self.location
            self.location = new_location
            logging.info(f"Camera {self.id}: Location changed from {old_location} to {new_location}")
            return f"Camera {self.id} location set to {new_location}"
        except Exception as e:
            logging.error(f"Camera {self.id}: Error setting location: {e}")
            raise e

def start_camera(camera_id, location, ip, port):
    try:
        camera = CameraIOT(camera_id, location)
        camera.setEncryption(KEY, upperCaseAll=False, removeSpace=False)
        camera.init_sockets(ip, port)

        # Start blockchain consensus TCP server in separate thread
        tcp_thread = threading.Thread(target=camera.start_TCP)
        tcp_thread.daemon = True
        tcp_thread.start()
        print(f"Camera {camera.id}: TCP server started for blockchain handling.")
        logging.info(f"Camera {camera_id}: Initialized at {location}, listening on {ip}:{port}")
        
        while True:
            try:
                # Use parent's receive method for encryption
                message, addr = camera.receive()
                logging.info(f"Camera {camera_id}: Received message: {message} from {addr}")
                
                if message == "exit":
                    break

                command, message = camera.parse_command(message)
                output = camera.process_command(command, message)

                # Use parent's send method for encryption
                logging.info(f"Camera {camera_id}: Sending response: {output}")
                camera.send(output, addr)
                
            except Exception as e:
                error_msg = f"Error in Camera {camera_id}: {str(e)}"
                logging.error(error_msg)
                try:
                    camera.send(error_msg, addr)
                except:
                    pass

        logging.info(f"Camera {camera_id}: Shutting down...")
    except Exception as e:
        logging.critical(f"Fatal error in Camera {camera_id}: {str(e)}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 4:
        logging.error("Camera initialization failed: Incorrect arguments provided.")
        print("Usage: python cameraIOT.py <camera_id> <location> <port>")
        print("Example: python cameraIOT.py cam1 'Front Door' 8081")
        sys.exit(1)

    try:
        camera_id = sys.argv[1]
        location = sys.argv[2]
        port = int(sys.argv[3])
        logging.info(f"Starting Camera with ID: {camera_id}, Location: {location}, Port: {port}")
        start_camera(camera_id, location, CAMERA_IP, port)
    except Exception as e:
        logging.critical(f"Fatal error starting Camera: {str(e)}")