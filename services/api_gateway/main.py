import uuid
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
import httpx
from shared.schemas import InspectionResponse

app = FastAPI(title="Agentic Anomaly Inspection Gateway")

CONFIDENCE_THRESHOLD = 0.70
IOU_THRESHOLD = 0.50

FEEDBACK_SERVICE_URL = "http://feedback_service:8001/v1/log_edge_case"
INFERENCE_ENGINE_URL = "http://inference_engine:8002/v1/predict"

async def dispatch_edge_case(payload: dict):
    async with httpx.AsyncClient() as client:
        try:
            await client.post(FEEDBACK_SERVICE_URL, json=payload, timeout=5.0)
        except Exception as e:
            print(f"[CRITICAL] Edge case dispatch failed: {str(e)}")

@app.get("/")
def read_root():
    return {"status": "API Gateway Running"}

@app.post("/v1/inspect", response_model=InspectionResponse)
async def inspect_frame(
    background_tasks: BackgroundTasks, 
    file: UploadFile = File(...)
):
    contents = await file.read()
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                INFERENCE_ENGINE_URL, 
                files={"file": (file.filename, contents, file.content_type)},
                timeout=5.0
            )
            eval_data = res.json()
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Inference Service unreachable: {str(e)}")

    confidence = eval_data["confidence"]
    iou_score = eval_data["iou_score"]
    inspection_id = str(uuid.uuid4())
    
    is_anomaly = confidence > CONFIDENCE_THRESHOLD
    status = "ACCEPTED"

    if confidence < CONFIDENCE_THRESHOLD or iou_score < IOU_THRESHOLD:
        status = "FLAGGED_FOR_AGENT_REVIEW"
        edge_case_payload = {
            "inspection_id": inspection_id,
            "timestamp": datetime.utcnow().isoformat(),
            "filename": file.filename,
            "confidence": confidence,
            "iou_score": iou_score,
            "raw_tensor_ref": f"/data/samples/{inspection_id}.bin",
            "status": "PENDING_REVIEW"
        }
        background_tasks.add_task(dispatch_edge_case, edge_case_payload)

    return InspectionResponse(
        inspection_id=inspection_id,
        timestamp=datetime.utcnow(),
        filename=file.filename,
        anomaly_detected=is_anomaly,
        confidence=confidence,
        iou_score=iou_score,
        status=status,
        predictions=eval_data.get("predictions", [])
    )
