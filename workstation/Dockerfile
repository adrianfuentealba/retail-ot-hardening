FROM debian:bookworm-slim
ARG TARGETARCH
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends xfce4 xfce4-terminal tigervnc-standalone-server tigervnc-common novnc websockify dbus-x11 curl ca-certificates python3 python3-venv sudo procps iproute2 net-tools openssl firefox-esr jq tcpdump && rm -rf /var/lib/apt/lists/*
COPY packages/osquery_${TARGETARCH}.deb /tmp/osquery.deb
RUN dpkg -i /tmp/osquery.deb && rm /tmp/osquery.deb
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir fastapi==0.115.8 uvicorn==0.34.0 httpx==0.28.1
RUN useradd -m -s /bin/bash student && mkdir -p /opt/retail /var/log/osquery /evidence
COPY agent.py labctl.py start.sh osquery.conf /opt/retail/
RUN ln -s /opt/retail/labctl.py /usr/local/bin/labctl && chmod +x /opt/retail/start.sh /opt/retail/labctl.py && printf 'student ALL=(root) NOPASSWD: /usr/bin/osqueryi\n' >/etc/sudoers.d/student-osquery
ENV PATH=/opt/venv/bin:$PATH PYTHONUNBUFFERED=1
WORKDIR /home/student
CMD ["/opt/retail/start.sh"]

RUN printf '{"name":"noVNC","version":"1.3.0"}\n' > /usr/share/novnc/package.json
