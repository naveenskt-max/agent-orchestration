from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import httpx
import random
from datetime import datetime, timedelta

app = FastAPI()

# Input Schema for sales_data_agent
class SalesDataAgentInput(BaseModel):
    time_period: str = Field(..., description="Time period for sales data (e.g., 'last_7_days', 'last_month', 'Q1_2024')")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Optional filtering criteria")

# Output Schema for sales_data_agent
class SalesRecord(BaseModel):
    date: str
    product_id: str
    amount: float
    category: str

class SalesDataAgentOutput(BaseModel):
    records: List[SalesRecord]
    total_sales: float
    period: str

@app.post("/execute", response_model=SalesDataAgentOutput)
async def execute(request: SalesDataAgentInput):
    # Generate synthetic sales data based on the time_period
    records = []
    total_sales = 0.0

    if request.time_period == "last_7_days":
        for i in range(7):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            for _ in range(random.randint(5, 15)): # 5 to 15 sales per day
                amount = round(random.uniform(10.0, 500.0), 2)
                product_id = f"PROD{random.randint(100, 999)}"
                category = random.choice(["Electronics", "Clothing", "Books", "Home Goods"])
                records.append(SalesRecord(date=date, product_id=product_id, amount=amount, category=category))
                total_sales += amount
        period_str = "last_7_days"
    elif request.time_period == "last_month":
        for i in range(30):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            for _ in range(random.randint(10, 30)): # 10 to 30 sales per day
                amount = round(random.uniform(20.0, 1000.0), 2)
                product_id = f"PROD{random.randint(100, 999)}"
                category = random.choice(["Electronics", "Clothing", "Books", "Home Goods", "Food"])
                records.append(SalesRecord(date=date, product_id=product_id, amount=amount, category=category))
                total_sales += amount
        period_str = "last_month"
    else:
        # Default or more generic period
        for _ in range(random.randint(20, 50)):
            date = datetime.now().strftime("%Y-%m-%d")
            amount = round(random.uniform(5.0, 200.0), 2)
            product_id = f"PROD{random.randint(100, 999)}"
            category = random.choice(["Electronics", "Clothing", "Books", "Home Goods"])
            records.append(SalesRecord(date=date, product_id=product_id, amount=amount, category=category))
            total_sales += amount
        period_str = request.time_period

    # Apply filters if any (mocking for now)
    if request.filters:
        # In a real scenario, this would filter the generated records
        print(f"Applying mock filters: {request.filters}")

    return SalesDataAgentOutput(records=records, total_sales=round(total_sales, 2), period=period_str)

@app.get("/health")
async def health_check():
    return {"status": "ok", "agent": "sales_data_agent"}

@app.on_event("startup")
async def register_agent():
    import os
    registry_host = os.getenv("REGISTRY_URL", "http://localhost:8000")
    registry_url = f"{registry_host}/register"
    agent_card = {
        "name": "sales_data_agent",
        "description": "Fetches sales records from database for specified time periods with filtering capabilities. Supports time-based queries and custom filtering.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "time_period": {
                    "type": "string",
                    "description": "Time period for sales data (e.g., 'last_7_days', 'last_month', 'Q1_2024')"
                },
                "filters": {
                    "type": "object",
                    "description": "Optional filtering criteria for sales records",
                    "properties": {
                        "min_amount": {"type": "number"},
                        "product_category": {"type": "string"}
                    }
                }
            },
            "required": ["time_period"]
        },
        "outputSchema": {
            "type": "object",
            "properties": {
                "records": {
                    "type": "array",
                    "description": "Array of sales records with details",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string"},
                            "product_id": {"type": "string"},
                            "amount": {"type": "number"},
                            "category": {"type": "string"}
                        }
                    }
                },
                "total_sales": {
                    "type": "number",
                    "description": "Sum of all sales amounts"
                },
                "period": {
                    "type": "string",
                    "description": "The time period that was queried"
                }
            }
        },
        "endpoint": "http://sales_data_agent:8001/execute"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(registry_url, json=agent_card)
            response.raise_for_status()
            print(f"Agent 'sales_data_agent' registered successfully with registry.")
    except httpx.RequestError as e:
        print(f"Failed to register agent 'sales_data_agent' with registry: {e}")
    except httpx.HTTPStatusError as e:
        print(f"Failed to register agent 'sales_data_agent' with registry, status code: {e.response.status_code}, response: {e.response.text}")

