# Multi-stage build for SDRIG Python SDK
# Stage 1: Builder
FROM python:3.12-slim AS builder

# Prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpcap-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim

LABEL maintainer="chubuchnyi@soda.auto" \
      description="SDRIG Python SDK - Control UIO/ELoad/IfMux devices via AVTP" \
      version="0.1.0"

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    SDRIG_LOG_LEVEL=INFO

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcap0.8 \
    iproute2 \
    tcpdump \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for better security
RUN groupadd -r sdrig && useradd -r -g sdrig sdrig

# Set working directory
WORKDIR /app

# Copy project files
COPY --chown=sdrig:sdrig . .

# Install SDRIG SDK in development mode
RUN pip install -e .

# Switch to non-root user
USER sdrig

# Default command shows help
CMD ["python", "-c", "from sdrig import SDRIG; help(SDRIG)"]

# Usage examples:
# Build:
#   docker build -t sdrig-sdk:latest .
#
# Run interactive shell:
#   docker run --rm -it --network host --cap-add NET_ADMIN --cap-add NET_RAW \
#     --env-file .env -v "$PWD/examples":/app/examples \
#     sdrig-sdk:latest /bin/bash
#
# Run specific example:
#   docker run --rm -it --network host --cap-add NET_ADMIN --cap-add NET_RAW \
#     --env-file .env sdrig-sdk:latest \
#     python examples/01_device_discovery.py
#
# Run tests:
#   docker run --rm sdrig-sdk:latest pytest tests/unit/ -v
#
# Development mode with volume mount:
#   docker run --rm -it --network host --cap-add NET_ADMIN --cap-add NET_RAW \
#     --env-file .env -v "$PWD":/app sdrig-sdk:latest /bin/bash
