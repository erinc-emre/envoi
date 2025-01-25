import socket
import json
import threading
import time
from packet import (
    BasePacket,
    MessagePacket,
    AckPacket,
)

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
        self.update_multicast_address(self.group_id)
        #self.seq_num = 0  # Initialize the sequence number
        # Lock for thread safety
        self.lock = threading.Lock()

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
        *update: need to use multicast here, previously it was broadcast

        :param packet: The BasePacket object to send.
        """
    
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            serialized_packet = packet.serialize()
            client_socket.sendto(serialized_packet, (self.MULTICAST_IP, self.MULTICAST_PORT))
            print(f"Sent {packet.get_packet_type()} packet to {self.MULTICAST_IP}:{self.MULTICAST_PORT}")

        
    
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

    def update_multicast_address(self, user_group):
        self.MULTICAST_IP = self.config["chat"]["groups"][user_group]["multicast_ip"]
        self.MULTICAST_PORT = self.config["chat"]["groups"][user_group]["multicast_port"]

    def receive_multicast(self):
        """
        Listens for multicast messages.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind to 0.0.0.0:PORT instead of the multicast IP
            sock.bind(("0.0.0.0", self.MULTICAST_PORT))

            # Join multicast group
            mreq = socket.inet_aton(self.MULTICAST_IP) + socket.inet_aton("0.0.0.0")
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            while self.is_running:
                try:
                    data, _ = sock.recvfrom(self.BUFFER_SIZE)
                    try:
                        packet = BasePacket.deserialize(data)
                        print(packet)
                    except Exception as e:
                        print(f"[Error] Failed to deserialize packet: {e}")
                except Exception as e:
                    print(f"[Error] Multicast reception failed: {e}")
                    break

    def process_message_packet(self, packet: MessagePacket):
        """
        Processes received message packets.
        """
        print(f"[Message Received] {packet}")
        # Directly handle sending the acknowledgment
        ack_packet = AckPacket(sender=self.client_id, recipient=packet.sender, seq_num=packet.seq_num)
        self.send_ack(ack_packet)

    def send_ack (self, packet: MessagePacket):
        # Send ACK packet using unicast to the server (you'll need to specify the server's IP and port)
        server_ip = self.config["network"][server_ip]  # Replace with the server's IP
        server_port = self.config["network"]["UNICAST_PORT"]
        #not sure if i need the above lines? 
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
            serialized_packet = packet.serialize()
            client_socket.sendto(serialized_packet, (server_ip, server_port))
            print(f"Sent ACK packet with seq_num {packet.seq_num} to {server_ip}:{server_port}")

        
        
    def start_client(self):
        """
        Starts the client to send and receive messages.
        """
        print("Welcome to the Chat App.")
        print("You are running as a client.")
        receive_thread = threading.Thread(target=self.receive_multicast, daemon=True)
        #retransmit_thread = threading.Thread(target=self.retransmit_packets, daemon=True)
        receive_thread.start()
        #retransmit_thread.start()
        try:
            while self.is_running:
                input_message = input("\n[Input] Type your message: ")
                if input_message.lower() == "exit":
                    print("[Info] Exiting...")
                    self.is_running = False
                    break
                packet = MessagePacket(sender=self.client_id, recipient=self.group_id, message=input_message, seq_num=self.seq_num,)
                self.send_packet(packet)
        except KeyboardInterrupt:
            print("\nClient stopped.")


if __name__ == "__main__":
    client = ChatClient()
    client.start_client()
