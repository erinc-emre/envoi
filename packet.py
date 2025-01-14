import datetime
import pickle
from abc import ABC, abstractmethod


class BasePacket(ABC):
    """
    Abstract base class for network packets in the chat application
    
    Attributes:
    - sender (str): Username or identifier of the message sender
    - recipient (str): Recipient of the message 
    - timestamp (float): Unix timestamp of when the packet was created
    """
    
    def __init__(self, sender: str, recipient: str):
        """
        Initialize a base packet
        
        :param sender: Username or identifier of the sender
        :param recipient: Recipient of the message
        """
        self.sender = sender
        self.recipient = recipient
        self.timestamp = datetime.datetime.now()

        print(self.timestamp)

    
    @abstractmethod
    def get_packet_type(self) -> str:
        """
        Abstract method to return the specific packet type
        
        :return: String representation of the packet type
        """
        pass
    
    def serialize(self):
        """Serializes the packet object into bytes using pickle."""
        return pickle.dumps(self)

    @classmethod
    def deserialize(cls, input):
        """Deserializes bytes into a Packet object."""
        return pickle.loads(input)
    
    def __str__(self):
        """
        String representation of the packet
        
        :return: Formatted string describing the packet
        """
        return f"[{self.timestamp}] {self.sender} -> {self.recipient}"


class MessagePacket(BasePacket):
    """
    Packet for standard chat messages
    """
    def __init__(self, sender: str, recipient: str, message: str):
        """
        Initialize a message packet
        
        :param sender: Sender of the message
        :param recipient: Recipient of the message
        :param message: Content of the message
        """
        super().__init__(sender, recipient)
        self.message = message
    
    def get_packet_type(self) -> str:
        return type(self).__name__
    
    def __str__(self):
        """
        String representation of the message packet
        
        :return: Formatted string describing the message
        """
        return f"{super().__str__()}: {self.message}"


class JoinPacket(BasePacket):
    """
    Packet for user join events
    """
    def get_packet_type(self) -> str:
        return type(self).__name__
    
    def __str__(self):
        """
        String representation of the join packet
        
        :return: Formatted string describing the join event
        """
        return f"{super().__str__()} joined the chat"


class LeavePacket(BasePacket):
    """
    Packet for user leave events
    """
    def get_packet_type(self) -> str:
        return type(self).__name__
    
    def __str__(self):
        """
        String representation of the leave packet
        
        :return: Formatted string describing the leave event
        """
        return f"{super().__str__()} left the chat"


class LeaderElectionStartPacket(BasePacket):
    """
    Packet to initiate leader election process
    """
    def get_packet_type(self) -> str:
        return type(self).__name__
    
    def __str__(self):
        """
        String representation of the leader election start packet
        
        :return: Formatted string describing the leader election start
        """
        return f"{super().__str__()} started leader election"


class LeaderAnnouncePacket(BasePacket):
    """
    Packet to announce the leader of the chat
    """
    def __init__(self, sender: str, recipient: str, leader_id: str):
        """
        Initialize a leader announce packet
        
        :param sender: Sender of the packet
        :param recipient: Recipient of the packet
        :param leader_id: Identifier of the new leader
        """
        super().__init__(sender, recipient)
        self.leader_id = leader_id
    
    def get_packet_type(self) -> str:
        return type(self).__name__
    
    def __str__(self):
        """
        String representation of the leader announce packet
        
        :return: Formatted string describing the leader announcement
        """
        return f"{super().__str__()} announced new leader: {self.leader_id}"


class ClientIpUpdatePacket(BasePacket):
    """
    Packet to update client IP addresses
    """
    def get_packet_type(self) -> str:
        return type(self).__name__
    
    def __str__(self):
        """
        String representation of the client IP update packet
        
        :return: Formatted string describing the client IP update
        """
        return f"{super().__str__()} updated IP addresses"


if __name__ == "__main__":
    # Example usage of the packet classes
    message_packet = MessagePacket("Alice", "Bob", "Hello, Bob!")
    print(message_packet)
    
    join_packet = JoinPacket("Alice", "Bob")
    print(join_packet)
    
    leave_packet = LeavePacket("Alice", "Bob")
    print(leave_packet)
    
    leader_election_start_packet = LeaderElectionStartPacket("Alice", "Bob")
    print(leader_election_start_packet)
    
    leader_announce_packet = LeaderAnnouncePacket("Alice", "Bob", "Charlie")
    print(leader_announce_packet)
    
    # Serialize and deserialize the packets
    serialized_packet = message_packet.serialize()
    deserialized_packet = BasePacket.deserialize(serialized_packet)
    print(deserialized_packet)
