import socket
import json
from packet import (
    MessagePacket,
)


# Configuration
def load_config():
    """
    Loads the configuration from a JSON file.

    :return: A dictionary containing the configuration parameters
    """
    with open("config.json", "r") as config_file:
        config = json.load(config_file)
    return config


# Load configuration
config = load_config()

BROADCAST_IP = config["network"]["BROADCAST_IP"]
BROADCAST_PORT = config["network"]["BROADCAST_PORT"]
BUFFER_SIZE = config["network"]["BUFFER_SIZE"]


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
        print(f"Sent {packet.get_packet_type()} packet to {broadcast_ip}:{broadcast_port}")


def authenticate():
    found_user = None
    while found_user is None:
        user_id_input = input("Please enter your user ID (e.g., @david99): ")

        if user_id_input in config["chat"]["users"]:
            found_user = config["chat"]["users"][user_id_input]
        else:
            print("User ID not found. Please try again.")

    if found_user:
        print(f"Welcome, {found_user['name']}!")

    return found_user


def get_group(user_id):
    # Find the group the user is part of
    user_group = None
    for group_id, group_info in config["chat"]["groups"].items():
        if user_id in group_info["users"]:
            user_group = group_id
            break

    if user_group:
        print(f"You are part of the group: {user_group}")
    else:
        print("You are not part of any group.")

    return user_group


def main():
    """
    Main function to demonstrate different packet types
    """

    print("Welcome to the Chat App.")
    print("You are running as a client.")

    client_data = authenticate()
    client_id = client_data["id"]
    group_id = get_group(client_id)

    while True:
        # Main thread for user input
        input_message = input("\n[Input] Type your message: ")
        if input_message.lower() == "exit":
            print("[Info] Exiting...")
            break

        packet = MessagePacket(sender=client_id,
                               recipient=group_id,
                               message=input_message)
        send_packet(packet, BROADCAST_IP, BROADCAST_PORT)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nClient stopped.")