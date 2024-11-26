import socket
import time
import json
from udp_packet import (
    Packet,
    PacketType,
)  

# Configuration
# Load configuration from config.yaml

with open('config.json', 'r') as config_file:
    config = json.load(config_file)


BROADCAST_IP = config["BROADCAST_IP"]
BROADCAST_PORT = config["BROADCAST_PORT"]
INTERVAL = 2


def send_packet(packet, broadcast_ip, broadcast_port):
    """
    Sends a serialized packet via UDP broadcast.

    :param packet: The Packet object to send.
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
        print(f"Sent {packet.packet_type} packet to {broadcast_ip}:{broadcast_port}")


if __name__ == "__main__":
    # Example usage of the Packet class
    packet = Packet("Alice", "Hello, Bob!")
    send_packet(packet, BROADCAST_IP, BROADCAST_PORT)

    # Send a broadcast packet every INTERVAL seconds

    while True:
        packet = Packet("Alice", "Hello, Bob!", PacketType.MESSAGE, "Bob", {})
        send_packet(packet, BROADCAST_IP, BROADCAST_PORT)
        time.sleep(INTERVAL)
