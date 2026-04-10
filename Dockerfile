FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV DLIB_NUM_THREADS=1
ENV CMAKE_BUILD_PARALLEL_LEVEL=1
ENV PIP_NO_CACHE_DIR=0

# ✅ apt retry config - network slow hoy to 5 var retry karse
RUN echo 'Acquire::Retries "5";' > /etc/apt/apt.conf.d/80-retries && \
    echo 'Acquire::http::Timeout "120";' >> /etc/apt/apt.conf.d/80-retries && \
    echo 'Acquire::ftp::Timeout "120";' >> /etc/apt/apt.conf.d/80-retries && \
    echo 'Acquire::Queue-Mode "access";' >> /etc/apt/apt.conf.d/80-retries

# ✅ Sequential download - parallel download band kari (network issue fix)
RUN echo 'APT::Acquire::Queue-Mode "access";' >> /etc/apt/apt.conf.d/80-retries

RUN apt-get update && apt-get install -y --fix-missing --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

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