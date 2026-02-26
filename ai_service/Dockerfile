FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY ai_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ai_service/ /app/ai_service/

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8001

# Command to run the application
CMD ["python", "ai_service/main.py"]
