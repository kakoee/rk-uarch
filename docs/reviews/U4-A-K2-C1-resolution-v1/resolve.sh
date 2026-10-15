#!/bin/sh
set -eu
# A private CONNECT allowlist, not a source/registry replacement or TLS interception.
# Cargo curl trace records HTTP requests/status; the proxy records DNS peers and tunnel outcomes.
perl /controls/connect-proxy.pl index /receipts/resolve-network.tsv /tmp/c1-proxy-ready &
proxy_pid=$!
trap 'kill "$proxy_pid" 2>/dev/null || true' EXIT HUP INT TERM
attempt=0
while [ ! -f /tmp/c1-proxy-ready ]; do
    attempt=$((attempt + 1))
    if [ "$attempt" -gt 20 ]; then exit 78; fi
    kill -0 "$proxy_pid"
    sleep 0.1
done
# No parent/image/global Cargo configuration or credentials may affect this operation.
for path in /.cargo/config /.cargo/config.toml /work/.cargo/config /work/.cargo/config.toml /root/.cargo/config /root/.cargo/config.toml /cargo-home/config /cargo-home/config.toml /cargo-home/credentials /cargo-home/credentials.toml; do
    test ! -e "$path" || exit 79
done
set +e
/usr/local/rustup/toolchains/1.99.0-x86_64-unknown-linux-gnu/bin/cargo update -p uarch-engine
result=$?
set -e
sleep 0.3
exit "$result"
