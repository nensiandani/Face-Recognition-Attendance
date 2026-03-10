# Dockerfile
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV DLIB_NUM_THREADS=1
ENV CMAKE_BUILD_PARALLEL_LEVEL=1
ENV PIP_NO_CACHE_DIR=1

# Install system deps required to build dlib / opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    git \
    libboost-all-dev \
    libopenblas-dev \
    liblapack-dev \
    libatlas-base-dev \
    libx11-dev \
    libjpeg-dev \
    zlib1g-dev \
    libgtk-3-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for caching
COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy app
COPY . .

# Collect static and migrate (optional at build time)
RUN python manage.py collectstatic --no-input || true
RUN python manage.py migrate --no-input || true

# Use the $PORT Render provides
EXPOSE 8000

CMD ["gunicorn", "visionai.wsgi:application", "--bind", "0.0.0.0:$PORT", "--workers", "3"]