FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Expose ports (will be mapped in docker-compose)
EXPOSE 7000 7001 7002 7003 8000

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "src.services.frontend_service:app", "--host", "0.0.0.0", "--port", "8000"]
