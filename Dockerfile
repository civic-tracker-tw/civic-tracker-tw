# ==============================================================================
# CivicTracker TW — Dockerfile
# Zero-dependency Python 3.13 Runtime for Antigravity Dual-Model Civic Tracker
# ==============================================================================

FROM python:3.13-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# Copy all source files
COPY . /app

# Compile human YAML config into machine protocol JSON at build time
RUN python -m backend.core.config_compiler

# Expose default port
EXPOSE 8080

# Run zero-dependency HTTP web server
CMD ["python", "-m", "backend.web_server", "--port", "8080", "--host", "0.0.0.0"]
