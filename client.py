import socket
import json
import threading
from packet import MessagePacket


class ChatClient:
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the client with configuration.

        :param config_path: Path to the configuration JSON file
        """
        self.config = self._load_config(config_path)
        self.BROADCAST_IP = self.config["network"]["BROADCAST_IP"]
        self.BROADCAST_PORT = self.config["network"]["BROADCAST_PORT"]
        self.BUFFER_SIZE = self.config["network"]["BUFFER_SIZE"]
        self.client_data = self.authenticate()
        self.client_id = self.client_data["id"]
        self.group_id = self.get_group(self.client_id)
        self.is_running = True

    def _load_config(self, config_path: str):
        """
        Loads the configuration from a JSON file.

        :param config_path: Path to the configuration file
        :return: A dictionary containing the configuration parameters
        """
        with open(config_path, "r") as config_file:
            return json.load(config_file)

    def send_packet(self, packet):
        """
        Sends a serialized packet via UDP broadcast.

        :param packet: The BasePacket object to send.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            serialized_packet = packet.serialize()
            client_socket.sendto(serialized_packet, (self.BROADCAST_IP, self.BROADCAST_PORT))
            print(f"Sent {packet.get_packet_type()} packet to {self.BROADCAST_IP}:{self.BROADCAST_PORT}")

    def authenticate(self):
        found_user = None
        while found_user is None:
            user_id_input = input("Please enter your user ID (e.g., @david99): ")
            if user_id_input in self.config["chat"]["users"]:
                found_user = self.config["chat"]["users"][user_id_input]
            else:
                print("User ID not found. Please try again.")
        print(f"Welcome, {found_user['name']}!")
        return found_user

    def get_group(self, user_id):
        user_group = None
        for group_id, group_info in self.config["chat"]["groups"].items():
            if user_id in group_info["users"]:
                user_group = group_id
                break
        print(f"You are part of the group: {user_group}" if user_group else "You are not part of any group.")
        return user_group

    def start_client(self):
        """
        Starts the client to send messages.
        """
        print("Welcome to the Chat App.")
        print("You are running as a client.")
        try:
            while self.is_running:
                input_message = input("\n[Input] Type your message: ")
                if input_message.lower() == "exit":
                    print("[Info] Exiting...")
                    self.is_running = False
                    break
                packet = MessagePacket(sender=self.client_id, recipient=self.group_id, message=input_message)
                self.send_packet(packet)
        except KeyboardInterrupt:
            print("\nClient stopped.")


if __name__ == "__main__":
    client = ChatClient()
    client.start_client()
