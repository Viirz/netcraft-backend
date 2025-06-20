FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Conditional startup based on FLASK_ENV
CMD if [ "$FLASK_ENV" = "production" ]; then \
        echo "Starting with Gunicorn (Production)"; \
        gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 --log-level info app:app; \
    else \
        echo "Starting with Flask dev server (Development)"; \
        python app.py; \
    fi