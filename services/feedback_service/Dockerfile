FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared /app/shared
COPY services/feedback_service /app/services/feedback_service
ENV PYTHONPATH=/app
CMD ["uvicorn", "services.feedback_service.main:app", "--host", "0.0.0.0", "--port", "8001"]
