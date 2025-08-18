# Stage 1: Build environment
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential

# Set working directory
WORKDIR /app

# Copy requirements and install with PyTorch CPU wheel
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install torch==2.1.1+cpu --extra-index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.txt

# Copy app code
COPY . .

# Expose port and run with Gunicorn
EXPOSE 8000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]