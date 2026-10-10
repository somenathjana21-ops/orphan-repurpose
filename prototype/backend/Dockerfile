FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libpq-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY README.md ./

# Create package structure stubs for editable install
RUN mkdir -p app/api/v1 app/core app/data app/db app/ml app/models app/services && \
    touch app/__init__.py app/api/__init__.py app/api/v1/__init__.py app/core/__init__.py app/db/__init__.py app/ml/__init__.py app/models/__init__.py app/services/__init__.py

# Install Python dependencies
RUN pip install --no-cache-dir -e ".[dev]"

# Copy source code
COPY app/ ./app/

# Create data and models directories
RUN mkdir -p /data /models

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]