# Stage 1: Build dependencies
FROM python:3.8-slim AS builder

WORKDIR /app

# Install only required build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install uv
RUN pip install --no-cache-dir --upgrade pip uv

# Copy only dependency files first (for caching)
COPY pyproject.toml uv.lock ./

# Install dependencies into the system
RUN uv pip install --system .

# Stage 2: Runtime
FROM python:3.8-slim

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Create app user
RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy app code to /app/iam
COPY . /app/iam

# Set permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose FastAPI port
EXPOSE 8000

# Run the app (you can change this to manage.py if needed)
CMD ["uvicorn", "iam.main:app", "--host", "0.0.0.0", "--port", "8000"]
