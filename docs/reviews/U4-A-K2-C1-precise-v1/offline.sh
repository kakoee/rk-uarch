#!/bin/sh
set -eu
for path in /.cargo/config /.cargo/config.toml /work/.cargo/config /work/.cargo/config.toml /work/native/.cargo/config /work/native/.cargo/config.toml /root/.cargo/config /root/.cargo/config.toml /cargo-home/config /cargo-home/config.toml /cargo-home/credentials /cargo-home/credentials.toml; do
    test ! -e "$path" || exit 79
done
exec "$@"
