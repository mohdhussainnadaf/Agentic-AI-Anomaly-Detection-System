FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY shared /app/shared
COPY services/mcp_agent /app/services/mcp_agent
ENV PYTHONPATH=/app
CMD ["python", "services/mcp_agent/tools.py"]
