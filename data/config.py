# IP ADDRESSES
HUB_IP = "192.168.56.1"  # Using each group members individual ip addresses
CAMERA_IP = "192.168.56.1"
DOORLOCK_IP = "192.168.56.1"
THERMOSTAT_IP = "192.168.56.1"

# PORTS
HUB_PORT = 8080

# Device Port Configurations
CAMERA_PORTS = {
    'cam1': 8081,
    'cam2': 8082,
    'cam3': 8083,
}

DOORLOCK_PORTS = {
    'door1': 8084,
    'door2': 8085,
    'door3': 8086,
}

THERMOSTAT_PORTS = {
    'therm1': 8087,
    'therm2': 8088,
    'therm3': 8089,
}

# For backward compatibility
CAMERA_PORT = CAMERA_PORTS['cam1']
DOORLOCK_PORT = DOORLOCK_PORTS['door1']
THERMOSTAT_PORT = THERMOSTAT_PORTS['therm1']

# SHARED SECRET KEY
KEY = 2