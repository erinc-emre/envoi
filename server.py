import socket
import json
from udp_packet import Packet  # Assuming your Packet class is in a file named packet.py


# Configuration
# Load configuration from config.json
# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

BROADCAST_IP = config["BROADCAST_IP"]
BROADCAST_PORT = config["BROADCAST_PORT"]
BUFFER_SIZE = config["BUFFER_SIZE"]

def start_server():
    """
    Starts the server to listen for incoming broadcast packets and prints them.
    """
    # Create a UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        # Allow the socket to reuse the address and port
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # This option may be platform-dependent
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # Bind the socket to listen on the broadcast port
        server_socket.bind((BROADCAST_IP, BROADCAST_PORT))
        print(f"Server is listening for broadcasts on port {BROADCAST_PORT}...")

        while True:
            try:
                # Receive data from a client
                data, address = server_socket.recvfrom(BUFFER_SIZE)
                print(f"Received data from {address}")

                # Deserialize the packet
                packet = Packet.deserialize(data)

                # Print packet details
                print(f"--------------------:")
                print(f"  Type: {packet.packet_type}")
                print(f"  Sender: {packet.sender}")
                print(f"  Data: {packet.data}")
                print(f"  Timestamp: {packet.timestamp}")
            except Exception as e:
                print(f"!!! --- Error processing packet: {e} --- !!!")

if __name__ == "__main__":
    start_server()