FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (needed for some python packages like lxml or numpy build)
RUN apt-get update && apt-get install -y \
    build-essential \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port (standard but often ignored by PaaS which sets dynamic port)
EXPOSE 8080

# Environment variable for Flask
ENV FLASK_APP=app.py

# Command to run on start
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--timeout", "120"]
