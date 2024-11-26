import time
from enum import Enum, auto
import pickle

class PacketType(Enum):
    """
    Enumeration of different packet types in the chat application
    """
    MESSAGE = auto() # Client Messages + Heartbeats
    JOIN = auto()
    LEAVE = auto()
    START_LEADER_ELECTION = auto()
    LEADER_ANNOUNCE = auto()

class Packet:
    """
    A class representing a network packet for a UDP-based chat application
    
    Attributes:
    - sender (str): Username or identifier of the message sender (client or server ID)
    - data (str): The actual content of the message
    - timestamp (float): Unix timestamp of when the packet was created
    - packet_type (PacketType): Type of the packet 
    - metadata (dict, optional): Additional metadata for the packet
    """
    
    def __init__(self, 
                 sender: str, 
                 recipient: str,
                 packet_type: PacketType, 
                 data: str):
        """
        Initialize a new packet
        
        :param sender: Username or identifier of the sender
        :param message: Content of the message
        :param packet_type: Type of the packet (default is MESSAGE)
        :param recipient: Recipient of the message (for private messages)
        :param metadata: Additional metadata dictionary
        """
        self.sender = sender
        self.data = data
        self.timestamp = None
        self.packet_type = packet_type
        self.recipient = recipient

    
    def __str__(self):
        """
        String representation of the packet
        
        :return: Formatted string describing the packet
        """
        base_str = f"[{time.ctime(self.timestamp)}] {self.sender}: {self.message}"
        if self.packet_type != PacketType.MESSAGE:
            base_str = f"{self.packet_type.name}: {base_str}"
        return base_str
    

    def serialize(self):
        """Serializes the packet object into bytes using pickle."""
        self.timestamp = time.time()
        return pickle.dumps(self)

    @staticmethod
    def deserialize(input):
        """Deserializes bytes into a Packet object."""
        return pickle.loads(input)
