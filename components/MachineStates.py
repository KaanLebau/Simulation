from enum import Enum

class MachineState(Enum):
    IDLE = "Idle"
    WORKING = "Working"
    STOPPED = "Stopped"
    WARNING = "Warning"


class PartState(Enum):
    PROCESSING = "Processing"
    PROCESSED = "Processed"
    RAW = "Raw"