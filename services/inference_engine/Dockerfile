FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared /app/shared
COPY services/inference_engine /app/services/inference_engine
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.inference_engine.predict:app", "--host", "0.0.0.0", "--port", "8002"]
