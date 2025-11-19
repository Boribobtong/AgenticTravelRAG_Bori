# Dockerfile for the FastAPI Application
# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /app
WORKDIR $APP_HOME

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . $APP_HOME

# Set the entrypoint to a safe script (although command is in docker-compose)
ENTRYPOINT ["/usr/local/bin/python"]

# Default command (overridden by docker-compose)
CMD ["src/api/main.py"]