import socket
import struct
import yaml

# Multicast settings (must match sender)

#read config 
with open("config.yaml") as f:
    config = yaml.safe_load(f)

MCAST_GRP = config["multicast"]["group"]
MCAST_PORT = config["multicast"]["port"]
MAX_PACKET_SIZE = config["multicast"]["max_packet_size"]
OUTPUT_FILE = 'received.jp2'

# How long to wait for more data (seconds)
RECEIVE_TIMEOUT = 15

# Create UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

# Bind to the port
sock.bind(('', MCAST_PORT))

# Join multicast group
mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

# Set a timeout to stop receiving after inactivity
sock.settimeout(RECEIVE_TIMEOUT)

print(f"Listening on multicast group {MCAST_GRP}:{MCAST_PORT}...")

received_data = bytearray()

try:
    while True:
        try:
            packet, _ = sock.recvfrom(MAX_PACKET_SIZE)
            received_data.extend(packet)
        except socket.timeout:
            print("No more packets. Assuming transfer is complete.")
            break
except KeyboardInterrupt:
    print("Interrupted by user.")
finally:
    sock.close()

# Write received bytes to file
with open(OUTPUT_FILE, 'wb') as f:
    f.write(received_data)

print(f"Received image saved as '{OUTPUT_FILE}'")
