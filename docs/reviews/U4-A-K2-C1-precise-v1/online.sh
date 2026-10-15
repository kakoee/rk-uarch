#!/bin/sh
set -eu
perl /controls/connect-proxy.pl archives /receipts/metadata-full-network.tsv /tmp/c1-proxy-ready &
proxy_pid=$!
trap 'kill "$proxy_pid" 2>/dev/null || true' EXIT HUP INT TERM
attempt=0
while [ ! -f /tmp/c1-proxy-ready ]; do
    attempt=$((attempt + 1))
    if [ "$attempt" -gt 20 ]; then exit 78; fi
    kill -0 "$proxy_pid"
    sleep 0.1
done
set +e
/bin/sh /controls/offline.sh "$@"
result=$?
set -e
sleep 0.3
exit "$result"
