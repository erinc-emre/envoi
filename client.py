import socket
import json
import threading
from packet import BasePacket, ChatMessagePacket, MissingChatMessagePacket
from console_printer import ConsolePrinter


class ConfigLoader:
    """Handles loading and parsing the configuration file."""

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
    """Chat client that handles authentication, message sending, and receiving."""

    def __init__(self, config_path="config.json"):
        self.config = ConfigLoader.load(config_path)
        self.is_running = True
        self.initialize_network()
        self.authenticate()
        self.message_queue = []
        self.latest_message = None

    def initialize_network(self):
        """Initializes network settings from the config file."""
        network_config = self.config.get("network", {})
        self.BROADCAST_IP = network_config.get("BROADCAST_IP", "255.255.255.255")
        self.BROADCAST_PORT = network_config.get("BROADCAST_PORT", 5000)
        self.BUFFER_SIZE = network_config.get("BUFFER_SIZE", 1024)

    def authenticate(self):
        """Prompts the user to enter their user ID and validates authentication."""
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
        """Finds and returns the group ID for the authenticated user."""
        for group_id, group_info in (
            self.config.get("chat", {}).get("groups", {}).items()
        ):
            if self.user_id in group_info.get("users", []):
                ConsolePrinter.info(f"You are part of the group: {group_id}")
                return group_id
        return None

    def setup_multicast(self):
        """Sets up multicast settings and initializes message queue."""
        group_info = self.config["chat"]["groups"][self.group_id]
        self.MULTICAST_IP = group_info["multicast_ip"]
        self.MULTICAST_PORT = group_info["multicast_port"]

    def send_broadcast(self, packet):
        """Sends a broadcast message to the network."""
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            client_socket.sendto(
                packet.serialize(), (self.BROADCAST_IP, self.BROADCAST_PORT)
            )
            ConsolePrinter.info(
                f"Sent {packet.get_packet_type()} packet to {self.BROADCAST_IP}:{self.BROADCAST_PORT}"
            )

    def receive_multicast(self):
        """Listens for incoming multicast messages."""
        with socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        ) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("0.0.0.0", self.MULTICAST_PORT))
            mreq = socket.inet_aton(self.MULTICAST_IP) + socket.inet_aton("0.0.0.0")
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            while self.is_running:
                try:
                    data, _ = sock.recvfrom(self.BUFFER_SIZE)
                    packet = BasePacket.deserialize(data)
                    if isinstance(packet, ChatMessagePacket):
                        self.handle_chat_message(packet)
                    ConsolePrinter.info(f"Packet received from: {packet.sender_id}")
                except Exception as e:
                    ConsolePrinter.error(f"[Error] Multicast receive error: {e}")

    def handle_chat_message(self, packet):

        print("[DEBUG] New Packet", packet.sequence["seq_id"], "--", packet.message)
        # ConsolePrinter.chat(packet)
        # self.message_queue

        ## First Message
        # Store the message
        if self.latest_message is None:
            # self.latest_message = packet
            self.message_queue.append(packet)

        ## Same Session ID - Same or Lower Sequence Number
        # Ignore the packet
        elif (
            packet.sequence["session_id"] == self.latest_message.sequence["session_id"]
            and packet.sequence["seq_id"] <= self.latest_message.sequence["seq_id"]
        ):
            return

        ## Same Session ID - Next Sequence Number
        # Store the message
        elif (
            packet.sequence["session_id"] == self.latest_message.sequence["session_id"]
            and packet.sequence["seq_id"] == self.latest_message.sequence["seq_id"] + 1
        ):
            # self.latest_message = packet
            self.message_queue.append(packet)

        ## Same Session ID - Higher Sequence Number but not the next
        # Store the message in the queue
        # Send a missing packet request
        elif (
            packet.sequence["session_id"] == self.latest_message.sequence["session_id"]
            and packet.sequence["seq_id"] > self.latest_message.sequence["seq_id"]
        ):

            if packet not in self.message_queue:
                self.message_queue.append(packet)

                missing_packet_sequence = self.latest_message.sequence
                missing_packet_sequence["seq_id"] += 1
                missing_packet = MissingChatMessagePacket(
                    sender_id=self.user_id,
                    chat_group=self.group_id,
                    missing_packet_sequence=missing_packet_sequence,
                )
                self.send_broadcast(missing_packet)

        ## Different Session ID
        # Reset the queue
        # Store the message
        elif (
            packet.sequence["session_id"] != self.latest_message.sequence["session_id"]
        ):
            self.message_queue = []
            self.latest_message = None
            self.message_queue.append(packet)

        ## Flush the queue
        self.message_queue.sort(key=lambda x: x.sequence["seq_id"])
        for message in self.message_queue:
            if (
                self.latest_message is None
                or message.sequence["seq_id"]
                == self.latest_message.sequence["seq_id"] + 1
            ):
                ConsolePrinter.chat(message)
                self.latest_message = message
                self.message_queue.remove(message)

    def start_client(self):
        """Starts the chat client, allowing users to send messages."""
        ConsolePrinter.info("Welcome to the Chat App.")
        threading.Thread(target=self.receive_multicast, daemon=True).start()
        try:
            while self.is_running:
                input_message = input("\n[Input] Type your message: ")
                if input_message.lower() == ":q":
                    ConsolePrinter.warning("Exiting application")
                    self.is_running = False
                    break
                if input_message.lower() == ":miss":
                    print("[DEBUG] Testing Missing Packet Functionality")
                    print(
                        "[DEBUG] Negative ACK SEQ_ID:  ",
                        self.latest_message.sequence["seq_id"],
                    )
                    print("[DEBUG] Negative ACK MSG   :  ", self.latest_message.message)
                    missing_packet_sequence = self.latest_message.sequence
                    missing_packet = MissingChatMessagePacket(
                        sender_id=self.user_id,
                        chat_group=self.group_id,
                        missing_packet_sequence=missing_packet_sequence,
                    )
                    self.send_broadcast(missing_packet)

                    continue
                packet = ChatMessagePacket(
                    sender_id=self.user_id,
                    message=input_message,
                    chat_group=self.group_id,
                )
                self.send_broadcast(packet)
        except KeyboardInterrupt:
            ConsolePrinter.warning("Client stopped.")
            self.is_running = False


if __name__ == "__main__":
    client = ChatClient()
    if client.is_running:
        client.start_client()
