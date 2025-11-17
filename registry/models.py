from pydantic import BaseModel, Field
from typing import Dict, Any, List

class AgentInputSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Any]
    required: List[str] = []

class AgentOutputSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Any]

class AgentCard(BaseModel):
    name: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    description: str
    inputSchema: AgentInputSchema
    outputSchema: AgentOutputSchema
    endpoint: str
