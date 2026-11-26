FROM rust:1.95-bookworm@sha256:6258907abe69656e41cd992e0b705cdcfabcbbe3db374f92ed2d47121282d4a1
RUN apt-get update && apt-get install -y --no-install-recommends \
    xvfb xauth openbox dbus-x11 at-spi2-core python3-pyqt5 \
    libatk-bridge2.0-0 libgtk-3-0 libgbm1 libasound2 libnss3 \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /build
COPY . .
RUN cargo fetch --locked --target x86_64-unknown-linux-gnu
RUN --network=none cargo build --jobs 2 --locked --offline --bin agent-desktop
