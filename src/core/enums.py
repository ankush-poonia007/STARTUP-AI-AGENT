from enum import Enum


class StartupStage(str, Enum):
    IDEA            =   "IDEA"
    MVP             =   "MVP"
    TRACTION        =   "TRACTION"
    GROWTH          =   "GROWTH"
    

class MessageRole(str, Enum):
    USER            =   "USER"
    ASSISTANT       =   "ASSISTANT"
    SYSTEM          =   "SYSTEM"
    

class MemoryType(str, Enum):
    STARTUP_FACT    =   "startup_fact"
    PREFERENCE      =   "preference"
    DECISION        =   "decision"
    GOAL            =   "goal"
    CONSTRAINT      =   "constraint"

    
class DocumentStatus(str, Enum):
    UPLOADED        =   "UPLOADED"
    PROCESSING      =   "PROCESSING"
    READY           =   "READY"
    FAILED          =   "FAILED"
    DELETED         =   "DELETED"
    

class WorkflowStatus(str, Enum):
    QUEUED          =   "QUEUED"
    RUNNING         =   "RUNNING"
    COMPLETED       =   "COMPLETED"
    FAILED          =   "FAILED"
    
