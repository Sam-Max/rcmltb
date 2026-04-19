FROM python:3.12-slim

WORKDIR /usr/src/app
RUN chmod 777 /usr/src/app && mkdir -p /usr/src/app/downloads && chmod 777 /usr/src/app/downloads

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD ["bash","start.sh"]
