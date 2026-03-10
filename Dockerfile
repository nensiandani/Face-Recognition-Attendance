FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV DLIB_NUM_THREADS=1
ENV CMAKE_BUILD_PARALLEL_LEVEL=1

RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libboost-all-dev \
    libatlas-base-dev \
    libopenblas-dev \
    liblapack-dev \
    libx11-dev \
    libgtk-3-dev \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . .

RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

RUN python manage.py collectstatic --no-input
RUN python manage.py migrate --no-input

EXPOSE 8000

CMD ["gunicorn", "visionai.wsgi:application", "--bind", "0.0.0.0:8000"]