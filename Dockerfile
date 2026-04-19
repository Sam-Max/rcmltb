FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    aria2 \
    bash \
    ca-certificates \
    curl \
    ffmpeg \
    git \
    gcc \
    build-essential \
    libmagic1 \
    p7zip-full \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    qbittorrent-nox \
    rclone \
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app && mkdir -p /usr/src/app/downloads && chmod 777 /usr/src/app/downloads

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash","start.sh"]
