FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV DLIB_NUM_THREADS=1
ENV CMAKE_BUILD_PARALLEL_LEVEL=1
ENV PIP_NO_CACHE_DIR=1

# Added python3-dev here (Crucial for dlib C++ compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

# Removed cmake from here to avoid the broken python wrapper
RUN pip install --upgrade pip setuptools wheel

RUN pip install -r requirements.txt

COPY . .

RUN python manage.py collectstatic --no-input || true
RUN python manage.py migrate --no-input || true

EXPOSE 8000

# Use 1 worker and 2 threads to save RAM, with a longer timeout
CMD ["gunicorn", "visionai.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "1", "--threads", "2", "--timeout", "120"]