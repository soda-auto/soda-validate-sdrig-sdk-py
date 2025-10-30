FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1


RUN apt-get update && apt-get install -y --no-install-recommends \
    libpcap0.8 libpcap0.8-dev build-essential iproute2 tcpdump ca-certificates \
 && rm -rf /var/lib/apt/lists/*


RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir scapy cantools libpcap
 
WORKDIR /app


ENTRYPOINT ["/bin/sh"]


#sudo docker build -t sdr-py-avtp .
#sudo docker run --rm -it --network host --cap-add NET_ADMIN --cap-add NET_RAW --env-file .env -v "$PWD/":/app --entrypoint /bin/bash sdr-py-avtp
