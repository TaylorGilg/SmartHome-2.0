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
#Initialize the camera with blockchain capabilities.
    def __init__(self, id, location="unknown"):
        super().__init__(id, "Camera", location)
        self.status = "live"
        self.location = location
        logging.info(f"Camera {id} initialized at location: {location}")
    
# Process commands received via TCP and log them to blockchain. Each command creates a new block in our chain for integrity.
    def process_command(self, command, message=None):
        """Process received command"""
        try:
            # Split command and MAC
            if "|" in command:
                command, _ = command.rsplit("|", 1) # Discard the MAC

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

            #display the blockchain
            #self.display_blockchain()

            logging.info(f"Command '{command}' executed successfully on Thermostat {self.id} with result: {result}")
            return str(result)

            #logging.info(f"Camera {self.id}: Command '{command}' executed successfully with result: '{result}'")
            #return result
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

# Initialize camera device with dual TCP servers
# 1. Main port - For encrypted device commands
# 2. Port+1000 - For blockchain consensus protocol
def start_camera(camera_id, location, ip, port):
    try:
        camera = CameraIOT(camera_id, location)
        camera.setEncryption(KEY, upperCaseAll=False, removeSpace=False)
        camera.init_sockets(ip, port)  # Initialize sockets first

        # Start blockchain consensus TCP server in separate thread which lets us handle blockchain syncing without blocking camera commands or corrupting the socket.
        tcp_thread = threading.Thread(target=camera.start_TCP)
        tcp_thread.daemon = True  # Thread ends when the program exits
        tcp_thread.start()  # Start thread
        print(f"Camera {camera.id}: TCP server started for blockchain handling.")

        logging.info(f"Camera {camera_id}: Initialized at {location}, listening on {ip}:{port}")
        
        # main processing loop for commands to continuosly accept TCP connections on the port and log blockchain processes.
        while True:
            try:
                # Accept incoming TCP connections
                conn, addr = camera.commSocket.accept()
                response = conn.recv(4096).decode("utf-8")
                logging.info(f"Camera {camera_id}: Received message: {response} from {addr}")
                if response == "exit":
                    break
                
                # Separate the MAC from the command
                if "|" in response:
                    response, _ = response.rsplit("|", 1) # Discard the MAC
                    print(f"Thermostat {camera_id} parsed command: {response.strip()}")

                # Parse and process the command
                command, message = camera.parse_command(response)
                output = camera.process_command(command, message)

                logging.info(f"Camera {camera_id}: Sending response: {output}")
                print(f"Camera {camera_id} sending response: {output}")
                print() # Spacing for clean output
                conn.sendall(output.encode("utf-8"))
                conn.close()
            except Exception as e:
                error_msg = f"Error in Camera {camera_id}: {str(e)}"
                logging.error(error_msg)
                conn.sendall(error_msg.encode("utf-8"))
                conn.close()

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