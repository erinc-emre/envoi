import socket
import json
from udp_packet import Packet  # Assuming your Packet class is in a file named packet.py


# Configuration
def load_app_config():
    """
    Loads the configuration from a JSON file.

    :return: A dictionary containing the configuration parameters
    """
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    return config["app_config"]


app_config = load_app_config()

config = load_app_config()

BROADCAST_IP = config["BROADCAST_IP"]
BROADCAST_PORT = config["BROADCAST_PORT"]
BUFFER_SIZE = config["BUFFER_SIZE"]

# Validate Sender
def validate_sender(sender):
    pass

# Validate Recipient
def validate_recipient(recipient):
    pass

# Forward Multicast
def forward_multicast():
    pass

# Forward Unicast
def forward_unicast():
    pass

# Heartbeat
def heartbeat():
    pass

# Load the list of chat responsibilities
def load_assign():
    pass

# Leader Election Start
def leader_election_start():
    pass

# Leader Election Announcement with the new leader and list of chat resposbilities
def leader_announce():
    pass


# Server Node Join
def join():
    pass

# Peaceful Server Node Shutdown
def leave():
    pass

# Initially clients IP addresses are known, but they may change over time
def client_ip_update():
    pass


def start_server():
    """
    Starts the server to listen for incoming broadcast packets and prints them.
    """
    # Create a UDP socket
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        # Allow the socket to reuse the address and port
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEPORT, 1
        )  # This option may be platform-dependent
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
