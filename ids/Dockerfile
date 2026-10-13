FROM ubuntu:24.04
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends suricata tcpdump tshark iproute2 python3 && rm -rf /var/lib/apt/lists/*
COPY start.sh packets.py retail.rules /opt/ids/
RUN chmod +x /opt/ids/start.sh
CMD ["/opt/ids/start.sh"]
