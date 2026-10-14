# ---- Store backend: FastAPI (Application 1) ----
FROM python:3.11-slim

WORKDIR /app

# Install dependencies first so Docker caches this layer when only code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY . .

# The SQLite file lives here; docker-compose mounts a volume on /app/data
# so orders survive restarts and redeploys.
ENV STORE_DB_DIR=/app/data

EXPOSE 8001

# No --reload in production: it's slower and watches files you don't need.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
