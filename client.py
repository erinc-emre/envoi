import socket
import time
import json
from packet import (
    MessagePacket,
    NodeDiscoveryPacket,
    NodeLeavePacket,
    LeaderElectionStartPacket,
    LeaderAnnouncePacket,
)


# Configuration
def load_config():
    """
    Loads the configuration from a JSON file.

    :return: A dictionary containing the configuration parameters
    """
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    return config["network"]


# Load configuration
config = load_config()

BROADCAST_IP = config["BROADCAST_IP"]
BROADCAST_PORT = config["BROADCAST_PORT"]
BUFFER_SIZE = config["BUFFER_SIZE"]

INTERVAL = 2
CLIENT_ID = "@alice24"


def send_packet(packet, broadcast_ip, broadcast_port):
    """
    Sends a serialized packet via UDP broadcast.

    :param packet: The BasePacket object to send.
    :param broadcast_ip: The IP address for broadcasting.
    :param broadcast_port: The port for broadcasting.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        # Enable broadcasting
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Serialize the packet
        serialized_packet = packet.serialize()

        # Send the packet
        client_socket.sendto(serialized_packet, (broadcast_ip, broadcast_port))
        print(
            f"Sent {packet.get_packet_type()} packet to {broadcast_ip}:{broadcast_port}"
        )


def main():
    """
    Main function to demonstrate different packet types
    """
    # Demonstrate different packet types in sequence
    packets = [
        # Message packet
        MessagePacket(
            sender=CLIENT_ID, recipient="+cat_persons_32", message="Hello, cat persons!"
        ),
        # Join packet
        NodeDiscoveryPacket(sender=CLIENT_ID, recipient="+cat_persons_32"),
        # Leader election start packet
        LeaderElectionStartPacket(sender=CLIENT_ID, recipient="+cat_persons_32"),
        # Leader announce packet
        LeaderAnnouncePacket(
            sender=CLIENT_ID, recipient="+cat_persons_32", leader_id="node-1"
        ),
        # Client IP update packet
        ClientIpUpdatePacket(sender=CLIENT_ID, recipient="+cat_persons_32"),
    ]

    # Send a different packet type every INTERVAL seconds
    while True:
        for packet in packets:
            send_packet(packet, BROADCAST_IP, BROADCAST_PORT)
            time.sleep(INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nClient stopped.")
