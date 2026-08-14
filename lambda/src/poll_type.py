from enum import Enum

class PollType(str, Enum):
    """Supported poll types."""
    STATUS = "STATUS"
    INFO = "INFO"
    TRIPS = "TRIPS"