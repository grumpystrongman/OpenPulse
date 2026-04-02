FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY packages/openpulse_core /app/packages/openpulse_core
COPY packages/openpulse_data /app/packages/openpulse_data
RUN pip install --no-cache-dir /app/packages/openpulse_core /app/packages/openpulse_data

COPY services /app/services
COPY standards /app/standards
COPY data-platform /app/data-platform
COPY docs /app/docs

ENV PYTHONPATH=/app:/app/packages/openpulse_core:/app/packages/openpulse_data
