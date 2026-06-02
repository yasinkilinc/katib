from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class Step(BaseModel):
    id: int = Field(..., description="Step sequence number")
    name: str = Field(..., description="Short name of the step")
    capability: str = Field(..., description="Capability to execute (e.g. web.search)")
    params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the capability")
    requires_feedback: bool = Field(False, description="If true, pause and wait for executor output")

class Plan(BaseModel):
    goal: str = Field(..., description="Summary of the user's intent")
    steps: List[Step] = Field(default_factory=list, description="List of steps to execute")
    reasoning: Optional[str] = Field(None, description="Reasoning behind the plan")
