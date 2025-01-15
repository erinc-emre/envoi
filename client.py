import socket
import json
import sys
import uuid
import threading
from packet import BasePacket, ChatMessagePacket


#TODO: Move sockets in to class, dont keep inside functions
#TODO: Close sockets properly on exit
#TODO: Pretty print the message to the console

class ChatClient:
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the client with configuration.

        :param config_path: Path to the configuration JSON file
        """
        self.config = self.load_config(config_path)
        self.BROADCAST_IP = self.config["network"]["BROADCAST_IP"]
        self.BROADCAST_PORT = self.config["network"]["BROADCAST_PORT"]
        self.BUFFER_SIZE = self.config["network"]["BUFFER_SIZE"]
        self.client_id = str(uuid.uuid1())
        self.user_id = self.authenticate()
        self.user_data = self.config["chat"]["users"][self.user_id]
        self.group_id = self.get_group(self.user_id)
        self.is_running = True

        self.MULTICAST_IP = self.config["chat"]["groups"][self.group_id]["multicast_ip"]
        self.MULTICAST_PORT = self.config["chat"]["groups"][self.group_id][
            "multicast_port"
        ]

    def logger(self, message):

        # sys.stdout.write(f"{self.user_id} [{datetime.now()}] {message}\n")
        sys.stdout.write(f"{self.client_id} || {message}\n")

    def load_config(self, config_path: str):
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
            client_socket.sendto(
                serialized_packet, (self.BROADCAST_IP, self.BROADCAST_PORT)
            )
            self.logger(
                f"Sent {packet.get_packet_type()} packet to {self.BROADCAST_IP}:{self.BROADCAST_PORT}"
            )

    def authenticate(self):
        try:
            while True:
                user_id_input = input("Please enter your user ID (e.g., @david99): ")
                if user_id_input in self.config["chat"]["users"].keys():
                    self.logger(f"User ID {user_id_input} authenticated.")
                    return user_id_input
                else:
                    print("User ID not found. Please try again.")
                    self.logger("Wrong user ID entered.")
        except KeyboardInterrupt:
            print("\nAuthentication stopped.")
            self.logger("Authentication stopped.")
            exit()

    def get_group(self, user_id):
        user_group = None
        for group_id, group_info in self.config["chat"]["groups"].items():
            if user_id in group_info["users"]:
                user_group = group_id
                break
        self.logger(
            f"You are part of the group: {user_group}"
            if user_group
            else "You are not part of any group."
        )
        return user_group

    def print_message(self, packet):
        #TODO: Pretty print the message to the console
        print(f"{packet.sender_id}: {packet.message}")

    def receive_multicast(self):
        """
        Listens for multicast messages.
        """
        with socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
        ) as sock:
            
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind to 0.0.0.0:PORT instead of the multicast IP
            sock.bind(("0.0.0.0", self.MULTICAST_PORT))

            # Join multicast group
            mreq = socket.inet_aton(self.MULTICAST_IP) + socket.inet_aton("0.0.0.0")
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            while self.is_running:
                try:
                    data, _ = sock.recvfrom(self.BUFFER_SIZE)

                    packet = BasePacket.deserialize(data)

                    if  isinstance(packet, ChatMessagePacket):
                        self.print_message(packet)


                    self.logger(f"Packet received from: {packet.sender_id}")


                except Exception as e:
                    self.logger(f"[Error] Multicast receive error: {e}")


    def start_client(self):
        """
        Starts the client to send and receive messages.
        """
        print("Welcome to the Chat App.")
        receive_thread = threading.Thread(target=self.receive_multicast, daemon=True)
        receive_thread.start()
        try:
            while self.is_running:
                input_message = input("\n[Input] Type your message: ")
                if input_message.lower() == "exit":
                    self.logger("Exiting application")
                    self.print_message("Exiting application")
                    self.is_running = False
                    break
                packet = ChatMessagePacket(
                    sender_id=self.user_id,
                    message=input_message,
                    chat_group=self.group_id,
                )
                self.send_packet(packet)
        except KeyboardInterrupt:
            self.logger("\nClient stopped.")

    def exit_client(self):
        self.is_running = False



if __name__ == "__main__":
    client = ChatClient()
    client.start_client()
