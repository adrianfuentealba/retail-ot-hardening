#!/bin/sh
set -eu
[ "$#" -eq 1 ] || { echo 'Uso: bash scripts/analyze-pcap.sh pcaps/archivo.pcap'; exit 2; }
tshark -r "$1" -Y 'modbus || opcua' -T fields -e frame.time -e ip.src -e ip.dst -e tcp.dstport -e modbus.func_code
