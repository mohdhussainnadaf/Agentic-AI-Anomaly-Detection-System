# Agentic AI Anomaly Detection & Inspection System

A decoupled, containerized microservices pipeline that ingests media streams, executes deep learning inference via ONNX Runtime, and routes low-confidence edge cases to an Agentic Feedback Loop using the Model Context Protocol (MCP).

## 🏗️ Architecture Overview
- **API Gateway**: FastAPI REST ingestion & async task delegation
- **Inference Engine**: ONNX Runtime anomaly scoring
- **Feedback Service**: Active learning queue backed by MongoDB
- **MCP Agent**: FastMCP tool-calling interface for agentic evaluation

## 🛠️ Quickstart
```bash
docker compose up -d
```
