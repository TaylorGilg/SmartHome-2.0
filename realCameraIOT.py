#**************************This is to be run on Micropython on ESP32 Cam module*****************************
import time
import camera
import network
import machine
import sys

import usocket
from machine import Pin
from config import *

from IOTdevice import IOTDevice

class ESPCamera(IOTDevice):
    status = 'off'
    f_pin = None 				# Flash Pin
    net = None					# Wifi network module
    cam = None					# Boolean for camera initialization
    frame_type = camera.FRAME_VGA
    
    def __init__(self, id):
        self.status = 'Camera is not Live'			
        self.f_pin = Pin(4, Pin.OUT)					# Define the flash pin
        self.net = network.WLAN(network.STA_IF)		# Initialize network
        self.flash(1)								# Starting initialization sequence
        self.setup_wifi()							# Setup Wi-Fi connection       
        
    def setup_wifi(self):
        """
            Set up Wi-Fi connection using config file
        """
        print('SSID: ', ssid)
        self.status = 'Initializing network connection'
        if not self.net.isconnected():
            try:        
                self.net.active(True)					# Setup network config
                self.net.connect(ssid, password)
            except Exception as e:
                print('Error: ', e)
                print('Network Status: ', self.net.isconnected())                
        timeout = 20
        while not self.net.isconnected() and timeout > 0:
            time.sleep(1)
            timeout -= 1           
        if self.net.isconnected():						# Indicate if Wi-Fi connection is successful
            print('Wi-Fi successfully connected')
            self.status = 'Network connection established; ' + 'Camera is not initialized'
            self.flash(2)
        else:
            print('Failed to connect Wi-Fi')
        self.ip = self.net.ifconfig()[0]
        print(self.net.ifconfig())        
        
    def flash(self, count=2):
        """
            Blink the Flash light on camera
        """
        count = min(9, count)
        if count == 0:
            self.f_pin.value(1)
            time.sleep(2)
            self.f_pin.value(0)
        else:       
            while count > 0:
                self.f_pin.value(1)
                time.sleep(0.5)
                self.f_pin.value(0)
                time.sleep(0.5)
                count -= 1
        time.sleep(2)
        return
    
    def init_camera(self):
        """
            Initialize camera 
        """
        try:
            self.cam = camera.init(0, format=camera.JPEG)
            print('Camera is live')
            self.status = 'Camera is live'
        except Exception as e:
            print('Error: ', e)
        return '200 - camera is live'
        
    def close_camera(self):
        """Close and deinitialize camera

        Returns:
            string: Confirmation of change
        """
        if self.cam is not None:
            print('Camera is being closed')
            camera.deinit()
        self.cam = False
        print('Camera is closed')
        return '200 - camera is closed'
        
    def get_status(self):
        """
            Report current status
        """ 
        return self.status
    
    def set_status(self, value):
        """
            Manually set current status
        """ 
        value = value.lower()
        if value == 'close':            
            self.close_camera()
            self.status = 'Camera is not initialized'
            return 'Camera is being turned off'
        else:
            return 'Invalid command'
        
    def init_sockets(self, ip, port):
        """
            Override init_socket due to IOT limitation
            Initialize TCP socket with hub here
        """
        self.setIP(ip)
        self.setPort(port)
        TCP_socket = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)
        TCP_socket.bind((self.ip, self.port))
        TCP_socket.listen(1)
        self.setSocket(TCP_socket)        
        return
    
    def get_frame_option(self):
        """Provide frame option to select from

        Returns:
            string: List of available options 
        """
        return "1-camera.FRAME_QVGA 2-camera.FRAME_VGA 3-camera.FRAME_SVGA 4-camera.FRAME_HD"
    
    def set_frame_option(self, opt):
        """Set image quality

        Args:
            opt (int): Picture quality of the image to select

        Returns:
            string: Confirmation of change
        """
        mapper = {
            '1': camera.FRAME_QVGA,
            '2': camera.FRAME_VGA,
            '3': camera.FRAME_SVGA,
            '4': camera.FRAME_HD
        }
        if opt is not None and opt in mapper:
            self.frame_type = mapper[opt]
            return "Frame option set"
        else:
            return "Invalid Option"
            
    def take_photo(self):
        """ Capture image and return the data """
        print("Capturing image.....")        
        camera.framesize(self.frame_type)
        try:
            self.flash(1)
            buf_data = camera.capture()
        except Exception as e:
            print("Camera Capture Failure")
            buf_data = "Error-Camera Capture Failed"
        return buf_data

    def process_command(self, command, message=None):
        """
        Args:
            command (string): Function to execute
            message (string, optional): Argument for the function. Defaults to None.

        Returns:
            string: Result of the function call
        """
        mapper = {
            'get_status': self.get_status,
            'camera_on': self.init_camera,
            'camera_off': self.close_camera,
            'take_photo': self.take_photo,
            'set_frame_option': self.set_frame_option,
            'get_frame_option': self.get_frame_option
        }
        if command in mapper:
            return mapper[command](message) if message else mapper[command]()
        else:
            return "Invalid command provided"


if __name__ == "__main__":    
    hub_net = ("192.168.68.59", 8085)
    camModule = ESPCamera('01')
    camModule.port = 8085
    
    # Set Encryption and socket
    camModule.setEncryption(2, upperCaseAll=False, removeSpace=False)
    camModule.init_sockets(camModule.ip, camModule.port)
    
    try:
        print("Listening for commands...")
        while True:
            conn, addr = camModule.commSocket.accept()
            response = conn.recv(4096).decode("utf-8")
            command, message = camModule.parse_command(response)
            
            if command == 'take_photo':
                if camModule.cam is None or not camModule.cam:
                    conn.sendall(b"Camera is not initialized")
                else:
                    output = camModule.process_command(command, message)
                    conn.sendall(output)
            else:
                output = camModule.process_command(command, message)
                conn.sendall(output.encode("utf-8"))
            conn.close()
    
    except Exception as e:
        print(e)
    finally:
        camModule.commSocket.close()
        camera.deinit()
        print('IOT has exited')