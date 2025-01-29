import socket
import json
import threading
from packet import BasePacket, ChatMessagePacket
from console_printer import ConsolePrinter


class ConfigLoader:
    @staticmethod
    def load(config_path="config.json"):
        try:
            with open(config_path, "r") as config_file:
                return json.load(config_file)
        except FileNotFoundError:
            ConsolePrinter.error("Configuration file not found.")
            exit(1)
        except json.JSONDecodeError:
            ConsolePrinter.error("Error parsing configuration file.")
            exit(1)


class ChatClient:
    def __init__(self, config_path="config.json"):
        self.config = ConfigLoader.load(config_path)
        self.is_running = True
        self.initialize_network()
        self.authenticate()

    def initialize_network(self):
        network_config = self.config.get("network", {})
        self.BROADCAST_IP = network_config.get("BROADCAST_IP", "255.255.255.255")
        self.BROADCAST_PORT = network_config.get("BROADCAST_PORT", 5000)
        self.BUFFER_SIZE = network_config.get("BUFFER_SIZE", 1024)

    def authenticate(self):
        while self.is_running:
            user_id_input = input("Please enter your user ID (e.g., @david99): ")
            if user_id_input in self.config.get("chat", {}).get("users", {}):
                self.user_id = user_id_input
                ConsolePrinter.info(f"User ID {user_id_input} authenticated.")
                self.group_id = self.get_group_id()
                if self.group_id:
                    self.setup_multicast()
                    return
                ConsolePrinter.error("You are not part of any group.")
            else:
                ConsolePrinter.warning("User ID not found. Please try again.")

    def get_group_id(self):
        for group_id, group_info in self.config.get("chat", {}).get("groups", {}).items():
            if self.user_id in group_info.get("users", []):
                ConsolePrinter.info(f"You are part of the group: {group_id}")
                return group_id
        return None

    def setup_multicast(self):
        group_info = self.config["chat"]["groups"][self.group_id]
        self.MULTICAST_IP = group_info["multicast_ip"]
        self.MULTICAST_PORT = group_info["multicast_port"]

    def send_broadcast(self, packet):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            client_socket.sendto(packet.serialize(), (self.BROADCAST_IP, self.BROADCAST_PORT))
            ConsolePrinter.info(f"Sent {packet.get_packet_type()} packet to {self.BROADCAST_IP}:{self.BROADCAST_PORT}")

    def receive_multicast(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", self.MULTICAST_PORT))
            mreq = socket.inet_aton(self.MULTICAST_IP) + socket.inet_aton("0.0.0.0")
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            while self.is_running:
                try:
                    data, _ = sock.recvfrom(self.BUFFER_SIZE)
                    packet = BasePacket.deserialize(data)
                    if isinstance(packet, ChatMessagePacket):
                        ConsolePrinter.chat(packet)
                    ConsolePrinter.info(f"Packet received from: {packet.sender_id}")
                except Exception as e:
                    ConsolePrinter.error(f"[Error] Multicast receive error: {e}")

    def start_client(self):
        ConsolePrinter.info("Welcome to the Chat App.")
        threading.Thread(target=self.receive_multicast, daemon=True).start()
        try:
            while self.is_running:
                input_message = input("\n[Input] Type your message: ")
                if input_message.lower() == "exit":
                    ConsolePrinter.warning("Exiting application")
                    self.is_running = False
                    break
                packet = ChatMessagePacket(sender_id=self.user_id, message=input_message, chat_group=self.group_id)
                self.send_broadcast(packet)
        except KeyboardInterrupt:
            ConsolePrinter.warning("Client stopped.")
            self.is_running = False


if __name__ == "__main__":
    client = ChatClient()
    if client.is_running:
        client.start_client()
