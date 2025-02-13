import pickle
import uuid
from abc import ABC, abstractmethod
import hashlib


class BasePacket(ABC):

    def __init__(self, sender_id: str):
        self.sender_id = sender_id
        self.id = uuid.uuid1()
        self.checksum = None

    def calculate_checksum(self):
        return hashlib.md5(str(self.id).encode()).hexdigest()

    def update_checksum(self):
        self.checksum = self.calculate_checksum()

    @abstractmethod
    def get_packet_type(self) -> str:
        pass

    def serialize(self):
        return pickle.dumps(self)

    @classmethod
    def deserialize(cls, input):
        return pickle.loads(input)

    def __str__(self):
        return f"{self.id}"


# Broadcast + Multicast packet
class ChatMessagePacket(BasePacket):

    def __init__(self, sender_id: str, message: str, chat_group: str):
        super().__init__(sender_id)
        self.message = message
        self.chat_group = chat_group

        # {session_id: uuid1, sequence:int}
        self.sequence = None

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"{super().__str__()}: {self.message}"


class MissingChatMessagePacket(BasePacket):

    def __init__(self, sender_id: str, chat_group: str, missing_packet_sequence: dict):
        super().__init__(sender_id)
        self.chat_group = chat_group
        self.missing_packet_sequence = missing_packet_sequence

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"{super().__str__()} || Missing Chat Message Request"


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
class LeaderElectionPacket(BasePacket):

    def __init__(self, sender_id: str, server_list: dict, leader_candidate: str, is_announcing: bool):
        super().__init__(sender_id)
        self.server_list = server_list
        self.leader_candidate = leader_candidate
        self.is_announcing = is_announcing

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        if self.is_announcing:
            return f"{super().__str__()} announced new leader: {self.leader_id}"
        else:
            return f"{super().__str__()} leader election in progress"


# Unicast packet
class HeartbeatPacket(BasePacket):

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"{super().__str__()} || Heartbeat"
