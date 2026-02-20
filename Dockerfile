FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy application files
COPY . .

# Create directory for templates if it doesn't exist
RUN mkdir -p templates static

# Initialize database
RUN python -c "import sqlite3; import os; from database import init_database; init_database()"

# Expose port
EXPOSE 10000

# Run the application
CMD ["gunicorn", "--config", "gunicorn_config.py", "app:app"]