# # Use the official Python image as base
# FROM python:3.11

# # Set the working directory in the container
# WORKDIR /app

# # Copy requirements and install dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the Django project files
# COPY . .

# # Expose port 8000 for Django
# EXPOSE 8000

# # Run database migrations, collect static files, and start the server
# CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"]









# **Stage 1: Builder**
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies for Python packages (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies separately
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# **Stage 2: Final Image**
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy installed Python dependencies from builder
COPY --from=builder /install /usr/local

# Copy Django project files
COPY . .

# Expose port 8000 for Django
EXPOSE 8000

# Run database migrations, collect static files, and start the server
CMD ["sh", "-c", "python manage.py migrate && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"]
