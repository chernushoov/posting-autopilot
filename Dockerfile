FROM python:3.11-slim

WORKDIR /app

# Build tools + Playwright/Chromium runtime libs.
# Chromium needs the GUI/audio shim libs even in headless mode.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdbus-1-3 libdrm2 libxkbcommon0 libatspi2.0-0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libpango-1.0-0 libcairo2 libasound2 \
    fonts-liberation fonts-noto-color-emoji \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install Chromium for Playwright once at build time so the worker
# container can post to Facebook groups without re-downloading at boot.
RUN python -m playwright install chromium

COPY . /app
