from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
import os

app = FastAPI(title="Active Learning Feedback Service")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo_db:27017")
client = AsyncIOMotorClient(MONGO_URI)
db = client.anomaly_detection

@app.post("/v1/log_edge_case")
async def log_edge_case(payload: dict):
    result = await db.edge_cases.insert_one(payload)
    return {"inserted_id": str(result.inserted_id), "status": "STORED"}

@app.get("/v1/edge_cases/pending")
async def get_pending_edge_cases(limit: int = 50):
    cursor = db.edge_cases.find({"status": "PENDING_REVIEW"}).limit(limit)
    cases = await cursor.to_list(length=limit)
    for c in cases:
        c["_id"] = str(c["_id"])
    return cases
