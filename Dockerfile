FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV DLIB_NUM_THREADS=1
ENV CMAKE_BUILD_PARALLEL_LEVEL=1
ENV PIP_NO_CACHE_DIR=1

# Install ONLY the required system deps for dlib and postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt .

# Install wheel and cmake via pip first to avoid dlib errors
RUN pip install --upgrade pip setuptools wheel cmake

# Install the rest of the requirements
RUN pip install -r requirements.txt

# Copy app
COPY . .

# Collect static and migrate
RUN python manage.py collectstatic --no-input || true
RUN python manage.py migrate --no-input || true

EXPOSE 8000

# Start Gunicorn server
CMD ["gunicorn", "visionai.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]