# CS Security Final Project Group 1 (Fall 2024)

## Participants 

- **Taylor Gilg**
- **Barsha Dhakal**
- **Aaqil Razak**
- **Tyler K Conwell**
- **Galavardino Sousa Jr.** 

## Contributions To The Project

- **Taylor Gilg**
Implemented Blockchain Consensus Protocol & TCP for Blockchain Communications.
- **Barsha Dhakal**
Implemented log files for hub and device general actions.
- **Aaqil Razak**
Implemented Blockchain Structure & Refactored General Communications from UDP to TCP.
- **Tyler K Conwell**
Refactored UI for Blockchain Demonstration.
- **Galavardino Sousa Jr.** 
Implemented MAC Authentication.

## Description

###  Authentication and Trust

This system simulates a network of peripheral IoT devices and a central hub. The previous group explored encryption techniques to prevent leakage of private information via network sniffing/spying and uphold confidentiality in communications between devices and hub. A vulnerability left to be explored was authentication and trust between entities in the network. 

Our demonstration utilizes blockchain structures to uphold integrity principles and, in the event a device is compromised, provide a way for the system to keep a reliable record of events. 

Each device has their own blockchain (similar to a linked list where each block is an object of properties that log individual device events and interactions). The hub periodically requests the chains of all devices. In the case that any of the devices have a differing record of events, the longest, valid chain is used to resolve conflicts. The hub then sends this resolved chain out to all the devices for them to update their own ledgers. 

## Notes
- We are currently experiencing issues with Windows devices due to strict porting and networking requirements
("Failed to send message: [WinError 10061] No connection could be made because the target machine actively refused it") but setting all devices to loopback address (127.0.0.1) can enable a full demo via the UI.
- RealCameraIOT.py was largely left untouched and not included in our scope of contributions since we did not have the hardware the original team had to accommodate its code. 

## How to Run
1. In config.py make sure all device and hub IP's match your own IP (use the ipconfig command in a command prompt terminal to find your personal IP address). 

2. Run desired devices (thermostatIOT.py, cameraIOT.py, doorlockIOT.py). Running each should open up respective terminals. There should be an example that prints in each terminal on how to format a command to instantiate the devices. 
- Usage: python thermostatIOT.py <therm_id> <location> <port>
- Example: python thermostatIOT.py therm1 'Living Room' 8087

3. Once the devices are all instantiated via the terminal you can run hubUI.py. A UI window should pop up. Here you can input the information for each device and click "Add Device" to register the devices. 
- Ex. (port and IP must match the values in config.py) 
- Device ID: therm1 
- Device IP: 192.168.2.5
- Device Port: 8087
- Device Location: Living Room

4. Send a command to the devices by clicking "Send Message." A new window should pop up where you can choose the device via a drop down menu and type a command from the list of respective device commands. Click "send" and there should be a response returned in the hub GUI and a record of the event should be observed via the device log and the blockchain log. 

- Messages between the hub and device should be visible over the network with Wireshark (tcp.port == <device port>). 
- Due to refactoring to TCP, the hub will no longer have the port number 8080.

### Running Notes
- When cloning from bit bucket you navigate to the project directory and press the clone button.
giving you the https and ssh cloning options.
- Then you can use git kracken or other service to clone a local copy and begin running the project with the above steps.
- May also need WireShark to be downloaded to see all parts of this project running as intended.

## Files

### Executables

- All devices (and hub) generate their own record keeping log (does not print blockchains).
- cameraIOT.py: simulates a security camera IoT device.
- doorlockIOT.py: simulates a smart door lock.
- hub.py: the main hub that commands all connected IoT devices.
- hubUI.py: GUI for hub.py
- realCameraIOT.py: executable that runs an actual security camera IoT (note: this file was not refactored for this contribution).
- thermostatIOT.py: simulates a thermostat

### Utility

- config.py: ports and ip addressed for hub and devices.
- Caesar.py: provides Caesar Cipher for devices.
- communicator.py: class inherited by all executable devices.
- Encryption.py: wrapper class for ciper implementations.
- IOTdevice.py: abstract class, implemented by actual IoT devices.
- README.md: project run instuctions, colaborators, and other inportant info.
- Vigenere.py: provides Vigenere Cipher for devices.
- Blockchain.py: imported by communicator, defines blockchain structures to be used by each device.
- Interaction.py: defines interactions by properties sender, recipient, and data for block structure.

## File Notes

- Some merge conflicts forced us to retool some of the work we had done leading up to the project, but we have a demo avaliable with most work.

## The research that inspired our project

Z. Berkay Celik, Leonardo Babun, Amit K. Sikder, Hidayet Aksu, Gang Tan, Patrick McDaniel, and A. Selcuk Uluagac. 2018. Sensitive information tracking in commodity IoT. In Proceedings of the 27th USENIX Conference on Security Symposium (SEC'18). USENIX Association, USA, 1687–1704.

## Research Archeology / Reference for Paper 

ARZT, S., RASTHOFER, S., FRITZ, C., BODDEN, E., BARTEL, A., KLEIN, J., LE TRAON, Y., OCTEAU, D., AND MCDANIEL, P. FlowDroid: Precise Context, Flow, Field, Object-sensitive and Lifecycle-aware Taint Analysis for Android Apps. ACM SIGPLAN Notices (2014).

## Paper Cited by

Han Yang, Carson Kuzniar, Chengyan Jiang, Ioanis Nikolaidis, and Israat Haque. 2024. Characterizing the Security Facets of IoT Device Setup. In Proceedings of the 2024 ACM on Internet Measurement Conference (IMC '24). Association for Computing Machinery, New York, NY, USA, 612–621. https://doi.org/10.1145/3646547.3688433

## Troubleshooting

- I am getting a UDP error!
UDP_socket.bind((self.ip, self.port))
OSError: [WinError 10049] The requested address is not valid in its context
Solution: Make sure the device's IP address in config.py matches the computer's actual address. (Double check your computer's IPv4 address using ipconfig)

- My messages are not sending!
Solution: Make sure the network you are connected to does not block the UDP ports you specified in config.py.

- hubUI is not running and throwing errors!
Solution: Make sure that the config.py has your ip in it.
Notes: This is found in the cmd by typing ipconfig

## Code Base Creators

- **Brent Hoover**
- **Jeffrey Hsu**
- **Mandil Pradhan**
- **April Valdez**
- **Viet Vu**
