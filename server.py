import socket
import json
import threading
from typing import Dict, Any, Optional
import subprocess
import uuid
import platform
import sys
import queue
import time

from packet import (
    BasePacket,
    MessagePacket,
    JoinPacket,
    LeavePacket,
    LeaderElectionStartPacket,
    LeaderAnnouncePacket,
    AckPacket,
)


class ChatServer:
    """
    A UDP broadcast chat server handling various packet types and server operations.
    """

    # Initialization
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the server with configuration and server state.

        :param config_path: Path to the configuration JSON file
        """
        
        
        # Track sequence numbers and acknowledgments
        self.acks= {} #used for storing ack messages recived in case of retranmission 
        self.timeout = 5 
        self.seq_num=0
        self.message_queue = []
        #locks for shared resources 
        self.seq_num_lock = threading.Lock()
        self.message_queue_lock = threading.Lock()
        self.acks_lock = threading.Lock()

        # Load configuration
        self.config = self._load_config(config_path)

        # Server network configuration
        self.BROADCAST_IP = self.config["network"]["BROADCAST_IP"]
        self.BROADCAST_PORT = self.config["network"]["BROADCAST_PORT"]
        self.MULTICAST_IP = self.config["network"]["MULTICAST_IP"]
        self.MULTICAST_PORT = self.config["network"]["MULTICAST_PORT"]
        self.SERVER_IP = self.get_server_ip()
        self.UNICAST_PORT = self.config["network"]["UNICAST_PORT"]
        self.BUFFER_SIZE = self.config["network"]["BUFFER_SIZE"]

        # Server state
        self.server_id = uuid.uuid1()
        self.is_leader = False
        self.current_leader = None

        # Communication sockets
        self.broadcast_socket: Optional[socket.socket] = None
        self.multicast_socket: Optional[socket.socket] = None
        self.unicast_socket: Optional[socket.socket] = None

        # Server Nodes in the network
        self.nodes = {
            self.server_id: {"server_ip": self.SERVER_IP, "is_leader": False},
        }

        self.clients = self.config["chat"]["users"]

    # Get Server IP

    def get_server_ip(self):
        os_name = platform.system()

        if os_name == "Linux":
            # Use hostname -I and awk for Linux
            try:
                return subprocess.getoutput("hostname -I | awk '{print $1}'")
            except Exception as e:
                print(f"Error retrieving IP on Linux: {e}")
                return None
        elif os_name == "Windows":
            # Use socket for Windows
            try:
                hostname = socket.gethostname()
                return socket.gethostbyname(hostname)
            except Exception as e:
                print(f"Error retrieving IP on Windows: {e}")
                return None
        elif os_name == "Darwin":  # macOS
            # Use socket or ifconfig for macOS
            try:
                result = subprocess.getoutput("ifconfig | grep 'inet ' | grep -v 127.0.0.1 | awk '{print $2}'")
                if result:
                    return result.split('\n')[0]  # Return the first found IP
                else:
                    hostname = socket.gethostname()
                    return socket.gethostbyname(hostname)
            except Exception as e:
                print(f"Error retrieving IP on macOS: {e}")
                return None
        else:
            print("Unsupported OS.")
            return None

    def get_multicast_address(self, user_group):
        return self.config["chat"]["groups"][user_group]["multicast_ip"],\
            self.config["chat"]["groups"][user_group]["multicast_port"]
    # Configuration
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Loads the configuration from a JSON file.

        :param config_path: Path to the configuration file
        :return: A dictionary containing the configuration parameters
        """
        try:
            with open(config_path, "r") as config_file:
                config = json.load(config_file)
            return config
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading configuration: {e}")
            return {}

    # Validation
    def _is_valid_sender(self, sender: str) -> bool:
        """
        OPTIONAL
        Validate the sender of a packet.

        :param sender: Sender identifier
        :return: Boolean indicating if sender is valid
        """
        pass

    def _is_valid_recipient(self, recipient: str) -> bool:
        """
        Validate the recipient of a packet.

        :param recipient: Recipient identifier
        :return: Boolean indicating if recipient is valid
        """
        return recipient in self.clients

    # Packet Handlers
    def _packet_handler(self, packet_data: bytes):
        """
        Deserialize and handle packets based on their type.

        :param packet_data: Serialized packet data
        """
        try:
            packet = BasePacket.deserialize(packet_data)

            if isinstance(packet, MessagePacket):
                self._message_handler(packet)
            elif isinstance(packet, JoinPacket):
                self._node_join(packet)
            elif isinstance(packet, LeavePacket):
                self._node_leave(packet)
            elif isinstance(packet, LeaderElectionStartPacket):
                self._leader_election(packet)
            elif isinstance(packet, LeaderAnnouncePacket):
                self._leader_announce(packet)
            elif isinstance(packet, AckPacket):
                self._ack_packet(packet)
                #added here 
            else:
                print(f"Unknown packet type: {packet.get_packet_type()}")
        except Exception as e:
            print(f"Error processing packet: {e}")

    def _message_handler(self, packet: MessagePacket):
        """
        Handle incoming chat messages and multicast them.

        :param packet: Message packet
        """
        with self.seq_num_lock:
            packet.seq_num= self.seq_num
            # Serialize the packet
            serialized_packet = packet.serialize()
            self.seq_num += 1

        multicast_ip, multicast_port = self.get_multicast_address(packet.recipient)
        print(f"[Message] {packet.sender} -> {packet.recipient}: {packet.message} (seq_num={self.seq_num})")
        print(f"[Multicast] Forwarded message to {multicast_ip}:{multicast_port}") 
        # Initial send
        self.multicast_socket.sendto(serialized_packet, (multicast_ip, multicast_port))
        

    def _node_join(self, packet: JoinPacket):
        """
        Handle new node joining the chat.

        :param packet: Join packet
        """
        pass

    def _node_leave(self, packet: LeavePacket):
        """
        Handle node leaving the chat.

        :param packet: Leave packet
        """
        pass

    def _leader_election(self, packet: LeaderElectionStartPacket):
        """
        Handle the start of leader election process.

        :param packet: Leader election start packet
        """
        pass

    def _leader_announce(self, packet: LeaderAnnouncePacket):
        """
        Leader only
        Handle leader announcement and chat responsibility distribution.

        :param packet: Leader announce packet
        """
        pass

    # Heartbeat Functions
    def _heartbeat(self):
        """
        Send heartbeats.

        """
        pass

    def _heartbeat_monitor(self):

        pass

    # Packet Listeners
    def _receive_broadcast_packets(self):
        """
        Continuous packet receiving thread.
        """
        while self.is_running:
            try:
                data, address = self.broadcast_socket.recvfrom(self.BUFFER_SIZE)
                print(f"Received data from {address}")
                self._packet_handler(data)
            except Exception as e:
                print(f"Error receiving packet: {e}")

    def _receive_multicast_packets(self):
        """
        Continuous packet receiving thread.
        """
        """
        Listens for multicast messages from group members.
        This function will handle incoming messages from clients, process them, and ensure sequence ordering.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind to the multicast port
            sock.bind(("", self.MULTICAST_PORT))
            #the socket can receive multicast packets sent to any interface

            # Join the multicast group
            mreq = socket.inet_aton(self.MULTICAST_IP) + socket.inet_aton("0.0.0.0")
            sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

            while self.is_running:
                try:
                    data, addr = sock.recvfrom(self.BUFFER_SIZE)
                    print(f"[Info] Received multicast message from {addr}")

                    # Deserialize the packet
                    packet = MessagePacket.deserialize(data)
                    self.process_received_message(packet)
                except Exception as e:
                    print(f"[Error] Failed to receive multicast packet: {e}")
                    break
    #recieving message packets from clients and putting them into the FIFO queue 
    def process_received_message (self, packet:MessagePacket):
        with self.message_queue_lock:
            self.message_queue.append(packet)

    def process_ack (self, packet: MessagePacket):
        seq_num= packet.seq_num
        with seq_num_lock:
            if seq_num not in self.acks:
                self.acks[seq_num]= set()
            self.acks[seq_num].add(packet.sender)

        group_members = self.config["chat"]["groups"][self.current_group_id]["users"]

        if len (self.acks[seq_num])==len(group_members):
            message_packet = next((msg for msg in self.message_queue if msg.seq_num == seq_num), None)
            # All clients have acknowledged, remove the message and send the next one
            with self.message_queue_lock:
                if message_packet:
                    self.message_queue.remove(message_packet)
                print(f"Message with seq_num {seq_num} removed from queue.")
                self.send_next_message()
        else: 
            self.retransmit_message(seq_num)
    def send_next_message(self):
        """
        Sends the next message in the queue and removes processed messages.
        """
        with self.message_queue_lock:
            # Now send the next message (if any) in the message queue
            if self.message_queue:
                self.message_queue.sort(key=lambda msg: msg.seq_num)
                next_message = self.message_queue.pop(0)  # Get the next message in line
        if next_message:
            print(f"Sending next message with seq_num {next_message.seq_num}")
            with self.acks_lock:    
                self.send_packet(next_message)

    def send_packet (self, packet: MessagePacket):
        """
    Serialize and send the packet using the appropriate socket.

    :param packet: The message packet to send
    """
    try:
        # Serialize the packet to bytes
        serialized_packet = packet.serialize()

        # Get the multicast address for the group
        multicast_ip, multicast_port = self.get_multicast_address(packet.recipient)
        if not self.multicast_socket:
            raise RuntimeError("Multicast socket is not initialized.")
        
        self.multicast_socket.sendto(serialized_packet, (multicast_ip, multicast_port))

        print(f"Sent multicast packet with seq_num {packet.seq_num} to {multicast_ip}:{multicast_port}")
    except Exception as e:
        print(f"Error sending packet: {e}")

    def retransmit_message(self, seq_num):
        #prevent ending too many messgaes at once 
        time.sleep(1)
        message_packet = next((msg for msg in self.message_queue if msg.seq_num == seq_num), None)
        if message_packet:
            print(f"Retransmitting message with seq_num {seq_num}")
            self.send_packet(message_packet)
   
    def _receive_unicast_packets(self):
        """
        Continuous packet receiving thread.
        """
        pass

    # Server Operations
    def start_server(self):
        """
        Start the server to listen for incoming packets.
        """
        try:
            # Setup Broadcast Socket
            self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.broadcast_socket.bind((self.SERVER_IP, self.BROADCAST_PORT))

            # Setup Multicast Socket
            self.multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
            self.multicast_socket.bind ((self.SERVER_IP, self.MULTICAST_PORT))
             # Join multicast group
            #mreq = socket.inet_aton(self.MULTICAST_IP) + socket.inet_aton("0.0.0.0")
            #self.multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            print(f"Server is listening on {self.SERVER_IP}:{self.BROADCAST_PORT}")

            self.is_running = True
            receive_broadcast_thread = threading.Thread(target=self._receive_broadcast_packets)
            receive_broadcast_thread.start()
            #receive_broadcast_thread.join()

            receive_multicast_thread = threading.Thread(target=self._receive_broadcast_packets)
            receive_multicast_thread.start()
            #receive_multicast_thread.join()

        except Exception as e:
            print(f"Server startup error: {e}")
        finally:
            if self.broadcast_socket:
                self.broadcast_socket.close()
            if self.multicast_socket:
                self.multicast_socket.close()

    def stop_server(self):
        """
        Gracefully stop the server.
        """
        self.is_running = False
        if self.broadcast_socket:
            self.broadcast_socket.close()
        if self.multicast_socket:
            self.multicast_socket.close()
        # TODO: What happens if we use TCP?
        if self.unicast_socket:
            self.unicast_socket.close()
        print("Server stopped.")


def main():
    """
    Main function to run the chat server.
    """
    server = ChatServer()
    try:
        server.start_server()
    except KeyboardInterrupt:
        server.stop_server()


if __name__ == "__main__":
    main()
