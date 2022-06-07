FROM ubuntu:latest

WORKDIR /usr/src/app
SHELL ["/bin/bash", "-c"]
RUN chmod 777 /usr/src/app

RUN apt-get -y update && DEBIAN_FRONTEND="noninteractive" \
    apt-get install -y python3 python3-pip qbittorrent-nox p7zip-full \
    p7zip-rar ffmpeg aria2 locales curl wget git unzip libmagic-dev libcrypto++-dev libssl-dev \ 
    libc-ares-dev libcurl4-openssl-dev libsqlite3-dev libsodium-dev libfreeimage-dev libpq-dev libffi-dev  \
    && locale-gen en_US.UTF-8 && \ 
    curl -L https://github.com/anasty17/megasdkrest/releases/download/latest/megasdkrest-$(cpu=$(uname -m);\
    if [[ "$cpu" == "x86_64" ]]; then echo "amd64"; elif [[ "$cpu" == "x86" ]]; \
    then echo "i386"; elif [[ "$cpu" == "aarch64" ]]; then echo "arm64"; else echo $cpu; fi) \
    -o /usr/local/bin/megasdkrest && chmod +x /usr/local/bin/megasdkrest && \ 
    curl https://rclone.org/install.sh | bash 

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash","start.sh"]