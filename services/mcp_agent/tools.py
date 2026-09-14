from mcp.server.fastmcp import FastMCP
import httpx
import json

mcp = FastMCP("Anomaly-Inspector-Agent")
FEEDBACK_SERVICE_URL = "http://feedback_service:8001/v1"

@mcp.tool()
async def inspect_db(limit: int = 10) -> str:
    """Queries stored low-confidence samples flagged by active learning."""
    async with httpx.AsyncClient() as client:
        res = await client.get(f"{FEEDBACK_SERVICE_URL}/edge_cases/pending?limit={limit}")
        return json.dumps(res.json(), indent=2)

@mcp.tool()
async def evaluate_edge_case(sample_id: str, verified_label: str) -> str:
    """Evaluates a flagged sample and updates state."""
    return f"Sample '{sample_id}' cataloged with label '{verified_label}'."

@mcp.tool()
async def trigger_retrain_pipeline(dataset_version: str, epochs: int = 50) -> str:
    """Triggers fine-tuning workflow when edge cases accumulate."""
    return f"Retraining job initialized for dataset '{dataset_version}' with {epochs} epochs."

if __name__ == "__main__":
    mcp.run()
