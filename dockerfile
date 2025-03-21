# Use Python 3.8 base image
FROM python:3.8-slim

# Set working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy the application code into the container
COPY . .

# Expose port 5000 (Flask default port)
EXPOSE 5000

# Environment variables
ENV PYTHONUNBUFFERED=1

# Run the Flask application
CMD ["python", "flask_apis.py"]
