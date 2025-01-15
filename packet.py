import datetime
import pickle
import uuid
from abc import ABC, abstractmethod


class BasePacket(ABC):

    def __init__(self, sender_id: str):
        self.sender_id = sender_id
        self.id = uuid.uuid1()

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


class ChatMessagePacket(BasePacket):

    def __init__(self, message: str):
        self.message = message

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"{super().__str__()}: {self.message}"


class NodeDiscoveryPacket(BasePacket):

    def __init__(self, sender_id: str, unicast_ip: str, unicast_port: int):
        super().__init__(sender_id)
        self.unicast_ip = unicast_ip
        self.unicast_port = unicast_port

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"Server Discovery Message || {super().__str__()} || IP: {self.unicast_ip}, Port: {self.unicast_port}"


class NodeDiscoveryReplyPacket(BasePacket):

    def __init__(self, sender_id: str, server_list: str):
        super().__init__(sender_id)
        self.server_list = server_list

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"Server Discovery Reply Message || {super().__str__()}"


class NodeLeavePacket(BasePacket):

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"{super().__str__()} || Server Leave Message"


class LeaderElectionStartPacket(BasePacket):

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"{super().__str__()} leader election started"


class LeaderAnnouncePacket(BasePacket):

    def __init__(self, sender_id: str, server_list: dict):
        super().__init__(sender_id)
        self.server_list = server_list

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"{super().__str__()} announced new leader: {self.leader_id}"


class ClientIpUpdatePacket(BasePacket):
#AcknowledgementPacket
    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return f"{super().__str__()} updated IP addresses"

class AcknowledgementPacket(BasePacket):
    def __init__(self, sender_id: str, acknowledged_packet_id: uuid.UUID, status: str = "Success"):

        super().__init__(sender_id)
        self.acknowledged_packet_id = acknowledged_packet_id
        self.status = status
        self.timestamp = datetime.datetime.now()

    def get_packet_type(self) -> str:
        return type(self).__name__

    def __str__(self):
        return (f"Acknowledgment || {super().__str__()} || "
                f"Acknowledged Packet ID: {self.acknowledged_packet_id} || "
                f"Status: {self.status} || Timestamp: {self.timestamp}")