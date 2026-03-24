FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV DLIB_NUM_THREADS=1
ENV CMAKE_BUILD_PARALLEL_LEVEL=1
ENV PIP_NO_CACHE_DIR=0

# ✅ --fix-missing add karyu - network error aave to retry karse
# ✅ rm -rf /var/lib/apt/lists/* hatavyu - cache rehese, fast rebuild
RUN apt-get update && apt-get install -y --fix-missing --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    python3-dev \
    libpq-dev

WORKDIR /app

COPY requirements.txt .

# ✅ Alag alag RUN commands - cache layer banse
RUN pip install --upgrade pip setuptools wheel
RUN pip install dlib-bin
RUN pip install -r requirements.txt

COPY . .

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]