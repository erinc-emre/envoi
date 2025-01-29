import argparse
from datetime import datetime, timedelta
import select
import struct
import time
import sys
import socket
import json
import threading
from typing import Dict, Any, Optional
import subprocess
import uuid
import platform

from packet import (
    BasePacket,
    ChatMessagePacket,
    NodeDiscoveryPacket,
    NodeDiscoveryReplyPacket,
    NodeLeavePacket,
    LeaderElectionStartPacket,
    LeaderAnnouncePacket,
    HeartbeatPacket,
    SequenceId
)


# TODO: Multiple servers can't start at the first DISCOVERY_TIMEOUT seconds

# TODO: Implement Logical Ring for leader election
# TODO: Implement LCR algorithm for leader election
# TODO: Implement heartbeat on the logical ring
# TODO: Implement server leave


class ChatServer:

    #
    # Initialization
    def __init__(self, config_path: str = "config.json"):

        # Load configuration
        self.config = self.load_config(config_path)

        # Server network configuration
        self.BROADCAST_IP = self.config["network"]["BROADCAST_IP"]
        self.BROADCAST_PORT = self.config["network"]["BROADCAST_PORT"]
        self.UNICAST_IP = self.get_server_ip()
        self.BUFFER_SIZE = self.config["network"]["BUFFER_SIZE"]
        self.DISCOVERY_TIMEOUT = self.config["network"]["DISCOVERY_TIMEOUT"]

        parser = argparse.ArgumentParser(description="Chat Server")
        parser.add_argument(
            "--unicast-port",
            type=int,
            required=True,
            help="Unicast port for the server",
        )
        args = parser.parse_args()
        self.UNICAST_PORT = args.unicast_port

        # Server state
        self.server_id = str(uuid.uuid1())
        self.is_leader = False
        self.current_leader = None
        self.is_running = False
        self.last_discovery_request_time = None

        self.discovery_reply_receive = threading.Event()

        # Communication sockets
        self.broadcast_socket: Optional[socket.socket] = None
        self.multicast_socket: Optional[socket.socket] = None
        self.unicast_socket: Optional[socket.socket] = None

        # Servers in the network
        self.server_list = {
            self.server_id: {
                "unicast_ip": self.UNICAST_IP,
                "unicast_port": self.UNICAST_PORT,
                "is_leader": self.is_leader,
                "chat_groups": [],
            },
        }

        # sequence_ids for each group chats
        self.chat_group_sequence_id = {}

        # Heartbeat
        self.last_seen_heartbeat = datetime.now()

    #
    # Configuration
    def load_config(self, config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, "r") as config_file:
                config = json.load(config_file)
            return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger(f"Error loading configuration: {e}")
            return {}

    #
    # Validation
    def is_valid_sender(self, sender: str) -> bool:
        pass

    def is_valid_recipient(self, recipient: str) -> bool:
        return recipient in self.config["chat"]["users"]

    #
    # Packet Sending
    def send_unicast(self, packet: BasePacket, recipient_ip: str, recipient_port: int):
        try:
            serialized_packet = packet.serialize()
            self.unicast_socket.sendto(
                serialized_packet, (recipient_ip, recipient_port)
            )
        except Exception as e:
            self.logger(f"Error sending unicast packet: {e}")

    def send_multicast(
        self, packet: BasePacket, recipient_ip: str, recipient_port: int
    ):
        try:
            serialized_packet = packet.serialize()
            self.multicast_socket.sendto(
                serialized_packet, (recipient_ip, recipient_port)
            )
        except Exception as e:
            self.logger(f"Error sending multicast packet: {e}")

    def send_broadcast(self, packet: BasePacket):

        try:
            serialized_packet = packet.serialize()
            self.broadcast_socket.sendto(
                serialized_packet, (self.BROADCAST_IP, self.BROADCAST_PORT)
            )
        except Exception as e:
            self.logger(f"Error sending broadcast packet: {e}")

    #
    # Packet Handlers
    def packet_handler(self, raw_packet: bytes, packet_ip: str, packet_port: int):

        try:
            packet = BasePacket.deserialize(raw_packet)

            if isinstance(packet, ChatMessagePacket):
                self.on_chat_message(
                    packet=packet, packet_ip=packet_ip, packet_port=packet_port
                )
            elif isinstance(packet, NodeDiscoveryPacket):
                self.on_node_discovery(
                    packet=packet, packet_ip=packet_ip, packet_port=packet_port
                )
            elif isinstance(packet, NodeDiscoveryReplyPacket):
                self.on_node_discovery_reply(
                    packet=packet, packet_ip=packet_ip, packet_port=packet_port
                )
            elif isinstance(packet, NodeLeavePacket):
                self.on_node_leave(
                    packet=packet, packet_ip=packet_ip, packet_port=packet_port
                )
            elif isinstance(packet, LeaderElectionStartPacket):
                self.on_leader_election(
                    packet=packet, packet_ip=packet_ip, packet_port=packet_port
                )
            elif isinstance(packet, LeaderAnnouncePacket):
                self.on_leader_announce(
                    packet=packet, packet_ip=packet_ip, packet_port=packet_port
                )
            elif isinstance(packet, HeartbeatPacket):
                self.on_heartbeat(
                    packet=packet, packet_ip=packet_ip, packet_port=packet_port
                )
            else:
                self.logger(f"Unknown packet type: {packet.get_packet_type()}")
        except Exception as e:
            self.logger(f"Error processing packet: {e}")

    def on_chat_message(
        self, packet: ChatMessagePacket, packet_ip: str, packet_port: int
    ):
        if not self.is_responsible_for_chat_group(packet.chat_group):
            return
        multicast_ip, multicast_port = self.get_multicast_group_addr(packet.chat_group)
        self.add_sequence_id_to_chat_message(packet)

        # Forward message to the multicast group
        self.send_multicast(packet, multicast_ip, multicast_port)
        self.logger(f"[Multicast] Forwarded message to {multicast_ip}:{multicast_port}")

    def on_node_discovery(
        self, packet: NodeDiscoveryPacket, packet_ip: str, packet_port: int
    ):

        if self.is_leader:
            # Check if the server already exists in the system
            if packet.sender_id in self.server_list:
                if packet.sender_id == self.server_id:
                    return
                else:
                    self.logger(
                        f"Server ID: {packet.sender_id} already exists in the system."
                    )
                    return

            self.server_list[packet.sender_id] = {
                "unicast_ip": packet.unicast_ip,
                "unicast_port": packet.unicast_port,
                "is_leader": False,
            }
            self.logger(f"Server ID: {packet.sender_id} Joined to the system")

            # Reply to the new server with the current server list
            reply_packet = NodeDiscoveryReplyPacket(
                sender_id=self.server_id, server_list=self.server_list
            )
            self.send_unicast(
                packet=reply_packet,
                recipient_ip=packet.unicast_ip,
                recipient_port=packet.unicast_port,
            )

    def on_node_discovery_reply(
        self, packet: NodeDiscoveryReplyPacket, packet_ip: str, packet_port: int
    ):
        # Set the event to indicate the reply is received
        # Breaks the discovery wait loop in the thread
        self.discovery_reply_receive.set()

        if datetime.now() - self.last_discovery_request_time < timedelta(seconds=5):

            self.server_list = packet.server_list
            self.logger("Joined to the existing system, Server list updated")

            # Start the leader election process
            leader_election_start_packet = LeaderElectionStartPacket(
                sender_id=self.server_id, server_list=self.server_list
            )
            self.send_unicast(leader_election_start_packet, packet_ip, packet_port)
        else:
            self.logger("Outdated discovery reply packet received")

    def on_node_leave(self, packet: NodeLeavePacket, packet_ip: str, packet_port: int):
        pass

    def on_leader_election(
        self, packet: LeaderElectionStartPacket, packet_ip: str, packet_port: int
    ):

        self.logger("Leader election process started")
        self.server_list = packet.server_list

        # TODO: TEMPORARY
        self.become_leader()

    def on_leader_announce(
        self, packet: LeaderAnnouncePacket, packet_ip: str, packet_port: int
    ):

        self.server_list = packet.server_list

        self.logger(f"Leader announced, Server list updated: {self.server_list}")

    def on_heartbeat(self, packet: HeartbeatPacket, packet_ip: str, packet_port: int):
        self.last_seen_heartbeat = datetime.now()

    #
    # Functionalities
    def become_leader(self):
        self.is_leader = True
        for server in self.server_list.values():
            server["is_leader"] = False
        self.server_list[self.server_id]["is_leader"] = True
        self.logger("Server is now the leader")
        self.distribute_chat_groups()

        leader_announce_packet = LeaderAnnouncePacket(
            sender_id=self.server_id, server_list=self.server_list
        )
        self.send_broadcast(leader_announce_packet)

    def distribute_chat_groups(self):

        chat_groups = self.config["chat"]["groups"]
        number_of_servers = len(self.server_list)

        # Distribute chat groups to servers as evenly as possible
        server_ids = list(self.server_list.keys())
        group_assignments = {server_id: [] for server_id in server_ids}

        for i, group in enumerate(chat_groups):
            server_id = server_ids[i % number_of_servers]
            group_assignments[server_id].append(group)

        # Update server list with group assignments
        for server_id, groups in group_assignments.items():
            self.server_list[server_id]["chat_groups"] = groups

    def logger(self, message):

        # sys.stdout.write(f"{self.server_id} [{datetime.now()}] {message}\n")
        sys.stdout.write(f"{self.server_id[:5]} || {message}\n")

    def uuid1_to_timestamp(self, uuid1):
        # Extract the timestamp components from the UUID
        timestamp = (uuid1.time - 0x01B21DD213814000) / 1e7  # Convert to seconds
        # UUID epoch starts at 1582-10-15, convert to standard datetime
        return datetime(1970, 1, 1) + timedelta(seconds=timestamp)

    def get_server_ip(self):
        os_name = platform.system()

        if os_name == "Linux":
            # Use hostname -I and awk for Linux
            try:
                return subprocess.getoutput("hostname -I | awk '{print $1}'")
            except Exception as e:
                self.logger(f"Error retrieving IP on Linux: {e}")
                return None
        elif os_name == "Windows":
            # Use socket for Windows
            try:
                hostname = socket.gethostname()
                return socket.gethostbyname(hostname)
            except Exception as e:
                self.logger(f"Error retrieving IP on Windows: {e}")
                return None
        elif os_name == "Darwin":  # macOS
            # Use socket or ifconfig for macOS
            try:
                result = subprocess.getoutput(
                    "ifconfig | grep 'inet ' | grep -v 127.0.0.1 | awk '{print $2}'"
                )
                if result:
                    return result.split("\n")[0]  # Return the first found IP
                else:
                    hostname = socket.gethostname()
                    return socket.gethostbyname(hostname)
            except Exception as e:
                self.logger(f"Error retrieving IP on macOS: {e}")
                return None
        else:
            self.logger("Unsupported OS.")
            return None

    def is_responsible_for_chat_group(self, chat_group):
        return chat_group in self.server_list[self.server_id]["chat_groups"]

    def add_sequence_id_to_chat_message(self, packet: ChatMessagePacket):
        chat_group = packet.chat_group
        if chat_group not in self.chat_group_sequence_id:
            self.chat_group_sequence_id[chat_group] = 0
        packet.add_seq_id(SequenceId(self.server_id, self.chat_group_sequence_id[chat_group]))
        self.chat_group_sequence_id[chat_group] += 1


    def get_multicast_group_addr(self, user_group):
        return (
            self.config["chat"]["groups"][user_group]["multicast_ip"],
            self.config["chat"]["groups"][user_group]["multicast_port"],
        )

    def get_right_logical_server(self):
        keys = list(self.server_list.keys())
        if self.server_id not in keys:
            raise ValueError("Current server ID not found in data.")

        current_index = keys.index(self.server_id)
        next_index = (current_index + 1) % len(
            keys
        )  # Modulo to wrap around to the first key
        return keys[next_index]

    def get_left_logical_server(self):
        keys = list(self.server_list.keys())
        if self.server_id not in keys:
            raise ValueError("Current server ID not found in data.")

        current_index = keys.index(self.server_id)
        next_index = (current_index - 1) % len(keys)
        return keys[next_index]

    #
    # Threads
    def receive_broadcast(self):

        self.logger(f"Listening {self.BROADCAST_IP}:{self.BROADCAST_PORT}")
        while self.is_running:
            try:
                data, addr = self.broadcast_socket.recvfrom(self.BUFFER_SIZE)
                self.packet_handler(
                    raw_packet=data, packet_ip=addr[0], packet_port=addr[1]
                )

            except Exception as e:
                self.logger(f"Error receiving a broadcast packet: {e}")

    def receive_unicast(self):

        self.logger(f"Listening {self.UNICAST_IP}:{self.UNICAST_PORT}")
        while self.is_running:
            try:
                data, addr = self.unicast_socket.recvfrom(self.BUFFER_SIZE)
                self.packet_handler(
                    raw_packet=data, packet_ip=addr[0], packet_port=addr[1]
                )

            except Exception as e:
                self.logger(f"Error receiving a unicast packet: {e}")

    def discovery_reply_wait(self):
        self.logger("Waiting for existing systems in the network")
        start_time = datetime.now()
        while True:
            if datetime.now() - start_time > timedelta(seconds=self.DISCOVERY_TIMEOUT):
                self.logger("No existing system found in the network")
                self.become_leader()
                break
            if self.discovery_reply_receive.is_set():
                self.logger("Existing system found in the network")
                break

    def send_heartbeat(self):
        heartbeat_packet = HeartbeatPacket(sender_id=self.server_id)
        while self.is_running:

            try:
                self.send_unicast(
                    packet=heartbeat_packet,
                    recipient_ip=self.server_list[self.get_right_logical_server()][
                        "unicast_ip"
                    ],
                    recipient_port=self.server_list[self.get_right_logical_server()][
                        "unicast_port"
                    ],
                )
            except Exception as e:
                self.logger(f"Error sending heartbeat: {e}")
            time.sleep(self.config["network"]["HEARTBEAT_INTERVAL"])
            self.logger(f"Heartbeat sent to {self.get_right_logical_server()}")

    def monitor_heartbeat(self):
        while self.is_running:
            if datetime.now() - self.last_seen_heartbeat > timedelta(
                seconds=self.config["network"]["HEARTBEAT_TIMEOUT"]
            ):
                self.logger(
                    f"Heartbeat timeout, server {self.get_left_logical_server()} is down."
                )

                # Give the server some time to recover
                self.last_seen_heartbeat = datetime.now()

                dead_server_id = self.get_left_logical_server()
                if len(self.server_list) == 2:

                    self.server_list.pop(dead_server_id)
                    self.logger(f"Server {dead_server_id} removed from the system")

                    self.become_leader()
                else:

                    self.server_list.pop(dead_server_id)
                    leader_election_start_packet = LeaderElectionStartPacket(
                        sender_id=self.server_id, server_list=self.server_list
                    )
                    self.send_unicast(
                        packet=leader_election_start_packet,
                        recipient_ip=self.server_list[self.get_right_logical_server()][
                            "unicast_ip"
                        ],
                        recipient_port=self.server_list[
                            self.get_right_logical_server()
                        ]["unicast_port"],
                    )

                time.sleep(1)

    #
    # Server Operations
    def start_server(self):

        self.is_running = True
        self.logger(f"Server Started")

        # Bind the broadcast socket
        try:
            # Setup Broadcast Socket
            self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            if platform.system() == "Windows":
                self.broadcast_socket.bind(("0.0.0.0", self.BROADCAST_PORT))
            else:
                self.broadcast_socket.bind((self.BROADCAST_IP, self.BROADCAST_PORT))
        except Exception as e:
            self.logger(f"Broadcast port binding error: {e}")

        # Bind the multicast socket
        try:

            self.multicast_socket = socket.socket(
                socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
            )
            try:
                if platform.system() == "Windows":
                    self.multicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                else:
                    self.multicast_socket.setsockopt(
                        socket.SOL_SOCKET, socket.SO_REUSEPORT, 1
                    )  # Optional, may not be available on all systems
            except AttributeError:
                print(
                    "SO_REUSEPORT is not supported on this system. Continuing without it."
                )

            # Set socket options for multicast
            ttl = struct.pack(
                "b", self.config["network"]["TTL"]
            )  # Time-to-live: 1 (local network)
            self.multicast_socket.setsockopt(
                socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl
            )

        except Exception as e:
            self.logger(f"Multicast port binding error: {e}")
            self.multicast_socket.close()

        # Bind the unicast socket
        try:
            self.unicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.unicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.unicast_socket.bind((self.UNICAST_IP, self.UNICAST_PORT))
        except Exception as e:
            self.logger(f"Unicast port binding error: {e}")

        # Start the broadcast listening thread
        try:
            receive_broadcast_thread = threading.Thread(target=self.receive_broadcast)

            receive_broadcast_thread.start()
        except Exception as e:
            self.logger(f"Broadcast listening thread error: {e}")

        # Start the unicast listening thread
        try:
            receive_unicast_thread = threading.Thread(target=self.receive_unicast)

            receive_unicast_thread.start()
        except Exception as e:
            self.logger(f"Unicast listening thread error: {e}")

        # Broadcast the discovery message
        discovery_packet = NodeDiscoveryPacket(
            sender_id=self.server_id,
            unicast_ip=self.UNICAST_IP,
            unicast_port=self.UNICAST_PORT,
        )
        self.send_broadcast(discovery_packet)
        self.last_discovery_request_time = datetime.now()

        # Start the discovery wait thread
        try:
            timeout_thread = threading.Thread(target=self.discovery_reply_wait)
            timeout_thread.start()
        except Exception as e:
            self.logger(f"Discovery wait thread error: {e}")

        # Heartbeat sending thread
        try:
            heartbeat_thread = threading.Thread(target=self.send_heartbeat)
            heartbeat_thread.start()
        except Exception as e:
            self.logger(f"Heartbeat thread error: {e}")

        # Heartbeat monitoring thread
        try:
            heartbeat_monitor_thread = threading.Thread(target=self.monitor_heartbeat)
            heartbeat_monitor_thread.start()
        except Exception as e:
            self.logger(f"Heartbeat monitor thread error: {e}")

    def stop_server(self):

        self.is_running = False
        if self.broadcast_socket:
            self.broadcast_socket.close()
        if self.multicast_socket:
            self.multicast_socket.close()
        # TODO: What happens if we use TCP?
        if self.unicast_socket:
            self.unicast_socket.close()
        self.logger("Server stopped.")


def main():

    server = ChatServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        server.stop_server()


if __name__ == "__main__":
    main()
