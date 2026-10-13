#!/bin/sh
set -eu
mkdir -p /evidence /captures
IFACE=$(ip -o -4 addr show | awk '$4 ~ /^172\.30\.40\./ {print $2; exit}')
[ -n "$IFACE" ] || { echo 'Control interface not found'; exit 1; }
tcpdump -Z root -U -n -i "$IFACE" -C 8 -W 3 -w /captures/live.pcap 'tcp port 502 or tcp port 4840' >/evidence/capture.log 2>&1 &
tshark -l -n -i "$IFACE" -f 'tcp port 502 or tcp port 4840' -T fields -E separator='|' -e frame.time_epoch -e ip.src -e tcp.srcport -e ip.dst -e tcp.dstport -e tcp.payload 2>/evidence/tshark.log | python3 /opt/ids/packets.py &
exec suricata -i "$IFACE" -c /etc/suricata/suricata.yaml -S /opt/ids/retail.rules -l /evidence --set stream.memcap=32mb --set flow.memcap=32mb
