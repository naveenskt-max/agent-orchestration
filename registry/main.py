from fastapi import FastAPI, HTTPException
from models import AgentCard
from storage import agent_storage

app = FastAPI()

@app.post("/register")
async def register_agent(agent_card: AgentCard):
    agent_storage.add_agent(agent_card)
    return {"message": f"Agent {agent_card.name} registered successfully."}

@app.get("/list_agents")
async def list_agents():
    return agent_storage.list_agents()

@app.post("/unregister")
async def unregister_agent(agent_name: str):
    agent = agent_storage.get_agent(agent_name)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent_storage.remove_agent(agent_name)
    return {"message": f"Agent {agent_name} unregistered successfully."}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
