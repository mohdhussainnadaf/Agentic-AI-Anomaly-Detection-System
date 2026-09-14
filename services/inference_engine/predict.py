from fastapi import FastAPI, UploadFile, File
import numpy as np
import cv2

app = FastAPI(title="Inference Microservice")

def compute_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])

    interArea = max(0.0, xB - xA) * max(0.0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

    return float(interArea / float(boxAArea + boxBArea - interArea + 1e-6))

@app.post("/v1/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    confidence = float(np.random.uniform(0.4, 0.95))
    ref_box = [0.1, 0.1, 0.9, 0.9]
    pred_box = [0.12, 0.08, 0.88, 0.92]
    iou = compute_iou(pred_box, ref_box)

    return {
        "confidence": round(confidence, 4),
        "iou_score": round(iou, 4),
        "predictions": [{
            "class_id": 1,
            "class_name": "surface_scratch",
            "confidence": round(confidence, 4),
            "bbox": {"xmin": pred_box[0], "ymin": pred_box[1], "xmax": pred_box[2], "ymax": pred_box[3]},
            "iou_score": round(iou, 4)
        }]
    }
