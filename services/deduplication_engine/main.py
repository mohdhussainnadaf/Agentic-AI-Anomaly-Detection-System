import os
import uuid
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from motor.motor_asyncio import AsyncIOMotorClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("deduplication_engine")

# Environment configurations
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongo_db:27017")
VECTOR_SIZE = 512  # Standard embedding dimension (e.g., CLIP / ResNet-18)
COLLECTION_NAME = "anomaly_embeddings"
SIMILARITY_THRESHOLD = 0.92  # 92% cosine similarity threshold

app = FastAPI(
    title="Vector Deduplication & Active Learning Service",
    version="2.0.0",
    description="Vector search service that prevents duplicate edge cases from cluttering the review queue."
)

# Initialize DB Clients
qdrant_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
mongo_client = AsyncIOMotorClient(MONGO_URI)
db = mongo_client["anomaly_detection"]


class VectorIngestPayload(BaseModel):
    inspection_id: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    embedding: List[float] = Field(..., min_items=VECTOR_SIZE, max_items=VECTOR_SIZE)
    metadata: dict = Field(default_factory=dict)


class IngestionResponse(BaseModel):
    status: str
    inspection_id: str
    similarity_score: Optional[float] = None
    matched_id: Optional[str] = None


@app.on_event("startup")
async def startup_event():
    """Ensure the Qdrant vector collection exists on application start."""
    try:
        if not qdrant_client.collection_exists(COLLECTION_NAME):
            qdrant_client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
            )
            logger.info(f"Created Qdrant collection: {COLLECTION_NAME}")
        else:
            logger.info(f"Connected to Qdrant collection: {COLLECTION_NAME}")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant collection: {e}")


@app.post("/v2/process_edge_case", response_model=IngestionResponse, status_code=status.HTTP_200_OK)
async def process_edge_case(payload: VectorIngestPayload):
    """
    Evaluates incoming low-confidence samples against Qdrant vector index.
    - If similarity >= 0.92: Increments duplicate counter in MongoDB.
    - If similarity < 0.92: Inserts new point into Qdrant & queues for Agentic Review.
    """
    try:
        # Search for near-identical vectors
        search_results = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=payload.embedding,
            limit=1,
            score_threshold=SIMILARITY_THRESHOLD
        )

        if search_results:
            matched_point = search_results[0]
            matched_id = matched_point.payload.get("inspection_id")
            score = matched_point.score

            # Increment duplicate frequency count in MongoDB
            await db.edge_cases.update_one(
                {"inspection_id": matched_id},
                {
                    "$inc": {"occurrence_count": 1},
                    "$push": {"duplicate_inspection_ids": payload.inspection_id},
                    "$set": {"last_seen_confidence": payload.confidence_score}
                }
            )
            logger.info(f"Duplicate anomaly detected ({score:.4f} similarity). Updated record {matched_id}.")

            return IngestionResponse(
                status="DUPLICATE_SUPPRESSED",
                inspection_id=payload.inspection_id,
                similarity_score=round(score, 4),
                matched_id=matched_id
            )

        # Unique vector: Register point in Qdrant
        point_uuid = str(uuid.uuid4())
        qdrant_client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_uuid,
                    vector=payload.embedding,
                    payload={"inspection_id": payload.inspection_id}
                )
            ]
        )

        # Persist as a new pending review case in MongoDB
        record = {
            "inspection_id": payload.inspection_id,
            "qdrant_point_id": point_uuid,
            "confidence_score": payload.confidence_score,
            "occurrence_count": 1,
            "status": "PENDING_AGENT_REVIEW",
            "metadata": payload.metadata
        }
        await db.edge_cases.insert_one(record)
        logger.info(f"New unique anomaly registered: {payload.inspection_id}")

        return IngestionResponse(
            status="QUEUED_FOR_REVIEW",
            inspection_id=payload.inspection_id
        )

    except Exception as e:
        logger.error(f"Error processing vector payload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
