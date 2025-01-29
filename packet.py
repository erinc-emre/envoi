import datetime
import pickle
import uuid
from abc import ABC, abstractmethod


class BasePacket(ABC):

    def __init__(self, sender_id: str):
        self.sender_id = sender_id

    @abstractmethod
    def get_packet_type(self) -> str:
        pass

    def serialize(self):
        return pickle.dumps(self)

    @classmethod
    def deserialize(cls, input):
        return pickle.loads(input)

    def __str__(self):
        return f"{self.sender_id}"


# Broadcast + Multicast packet
class ChatMessagePacket(BasePacket):

    def __init__(self, sender_id: str, message: str, chat_group: str):
        super().__init__(sender_id)
        self.message = message
        self.chat_group = chat_group
        self.seq_id = None

    def get_packet_type(self) -> str:
        return type(self).__name__

    def add_seq_id(self, seq_id):
        self.seq_id = seq_id

    def get_seq_id(self):
        return self.seq_id

    def __str__(self):
        return f"{super().__str__()}: {self.message}"


class SequenceId:
    def __init__(self, server_id, counter):
        self.server_id = server_id
        self.counter = counter

    def is_same_server_id(self, seq_id):
        return self.server_id == seq_id.server_id

    def is_incoming_next_counter(self, seq_id):
        return seq_id.counter - self.counter == 1

    def is_incoming_smaller_counter(self, seq_id):
        return seq_id.counter - self.counter < 0

# Broadcast packet
class NodeDiscoveryPacket(BasePacket):

    def __init__(self, sender_id: str, unicast_ip: str, unicast_port: int):
        super().__init__(sender_id)
        self.unicast_ip = unicast_ip
        self.unicast_port = unicast_port

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"Server Discovery Message || {super().__str__()} || IP: {self.unicast_ip}, Port: {self.unicast_port}"


# Unicast packet
class NodeDiscoveryReplyPacket(BasePacket):

    def __init__(self, sender_id: str, server_list: str):
        super().__init__(sender_id)
        self.server_list = server_list

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"Server Discovery Reply Message || {super().__str__()}"


# Unicast packet
class NodeLeavePacket(BasePacket):

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"{super().__str__()} || Server Leave Message"


# Unicast packet
class LeaderElectionStartPacket(BasePacket):

    def __init__(self, sender_id: str, server_list: dict):
        super().__init__(sender_id)
        self.server_list = server_list

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"{super().__str__()} leader election started"


# Broadcast packet
class LeaderAnnouncePacket(BasePacket):

    def __init__(self, sender_id: str, server_list: dict):
        super().__init__(sender_id)
        self.server_list = server_list

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"{super().__str__()} announced new leader: {self.leader_id}"


# Unicast packet
class HeartbeatPacket(BasePacket):

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"{super().__str__()} || Heartbeat"