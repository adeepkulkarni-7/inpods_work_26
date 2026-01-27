# Curriculum Mapping Service - Docker Image
#
# Build:
#   docker build -t curriculum-mapping:latest .
#
# Run:
#   docker run -p 5001:5001 --env-file .env curriculum-mapping:latest

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies for matplotlib
RUN apt-get update && apt-get install -y \
    libfreetype6-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy integration package
COPY integration/ ./integration/

# Copy additional files
COPY .env.example .env.example

# Create necessary directories
RUN mkdir -p uploads outputs outputs/insights outputs/library

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=5001

# Expose port
EXPOSE 5001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/api/health')" || exit 1

# Run the application
CMD ["python", "-m", "integration.app"]
