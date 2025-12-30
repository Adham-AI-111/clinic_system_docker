# Stage 1: Builder (optional for caching, but simpler to install in final stage)
FROM python:3.13-slim AS builder

WORKDIR /app

# Environment variables to optimize Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Upgrade pip and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Stage 2: Production
FROM python:3.13-slim

# Create non-root user
RUN useradd -m -r appuser && mkdir /app && chown -R appuser /app

WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8001

# Start the application
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "3", "clinic_system.wsgi:application"]
