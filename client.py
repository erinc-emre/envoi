import socket
import time
import json
from udp_packet import (
    Packet,
    PacketType,
)


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

INTERVAL = 2
CLIENT_ID = "@alice24"


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
    # Send a broadcast packet every INTERVAL seconds

    while True:
        packet = Packet(
            sender=CLIENT_ID,
            recipient="+cat_persons_32",
            packet_type=PacketType.MESSAGE,
            data="Hello, cat persons!",
        )
        send_packet(packet, BROADCAST_IP, BROADCAST_PORT)
        time.sleep(INTERVAL)
