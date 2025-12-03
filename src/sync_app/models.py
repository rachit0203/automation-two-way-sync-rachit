from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class LeadStatus(str, Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    LOST = "LOST"


class TaskStatus(str, Enum):
    TODO = "TODO"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"


class Lead(BaseModel):
    id: str
    name: str
    email: str
    status: LeadStatus
    source: Optional[str] = None


class Task(BaseModel):
    id: str
    title: str
    status: TaskStatus
    lead_id: str = Field(..., alias="leadId")
    notes: Optional[str] = None
