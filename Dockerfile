# Use Python 3.11 slim image for production deployment
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# Set working directory
WORKDIR /app

# Install system dependencies required for scientific computing
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libfontconfig1 \
    libfreetype6 \
    && rm -rf /var/lib/apt/lists/*

# Create directories for application
RUN mkdir -p /app/results/raw_output /app/results/synthetic /app/logs /app/reports/images

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 app \
    && chown -R app:app /app

# Switch to non-root user
USER app

# Health check for container
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from database import BenchmarkDatabase; db = BenchmarkDatabase(); db.get_runs()" || exit 1

# Expose port for web UI
EXPOSE 5000

# Default command - start web dashboard
CMD ["python", "web/dashboard.py", "--host", "0.0.0.0", "--port", "5000"]
