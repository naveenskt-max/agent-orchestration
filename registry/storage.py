from typing import Dict, Union
from models import AgentCard

class AgentStorage:
    def __init__(self):
        self.agents: Dict[str, AgentCard] = {}

    def add_agent(self, agent_card: AgentCard):
        self.agents[agent_card.name] = agent_card

    def get_agent(self, agent_name: str) -> Union[AgentCard, None]:
        return self.agents.get(agent_name)

    def list_agents(self) -> list[AgentCard]:
        return list(self.agents.values())

    def remove_agent(self, agent_name: str):
        if agent_name in self.agents:
            del self.agents[agent_name]

agent_storage = AgentStorage()
