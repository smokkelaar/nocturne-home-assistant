# Both API and web are compiled from the same checksum-verified Personal source.
FROM node:24.18.0-bookworm-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS node
FROM rust@sha256:4673f78db88b71f09d5451bbc404734807918161241215ba0a50bbbe9b448117 AS rust
FROM mcr.microsoft.com/dotnet/sdk@sha256:0e53453ccfc8ff2d51319fe80c678971c6d0f8008dff3565fa88e15840b69854 AS source
COPY --from=node /usr/local/ /usr/local/
COPY --from=rust /usr/local/cargo/ /usr/local/cargo/
COPY --from=rust /usr/local/rustup/ /usr/local/rustup/
ENV CARGO_HOME=/usr/local/cargo RUSTUP_HOME=/usr/local/rustup PATH=/usr/local/cargo/bin:$PATH
ENV DOTNET_CLI_TELEMETRY_OPTOUT=1 NODE_OPTIONS=--max-old-space-size=6144
RUN apt-get update && apt-get install -y --no-install-recommends build-essential pkg-config libssl-dev ca-certificates \
    && npm install -g pnpm@10.13.1
ADD --checksum=sha256:732462191524ab375b22bc6680e90ec8273367dd688115dec8629ce312a388df https://codeload.github.com/smokkelaar/nocturne-personal/tar.gz/4d9b4c9e434b0951a01a2f5409503c03f838f0ec /tmp/source.tar.gz
RUN mkdir /src && tar -xzf /tmp/source.tar.gz --strip-components=1 -C /src
WORKDIR /src/src/Web
RUN pnpm install --frozen-lockfile && pnpm --filter @nocturne/bridge run build
WORKDIR /src
RUN dotnet build src/API/Nocturne.API/Nocturne.API.csproj -c Release -p:UseSharedCompilation=false
RUN cargo build --manifest-path crates/Cargo.toml --release --locked -p nocturne-alerts-ffi
RUN dotnet publish src/API/Nocturne.API/Nocturne.API.csproj -c Release -r linux-x64 --self-contained false \
    -p:GenerateNSwagClient=false -p:UseSharedCompilation=false -o /out/api
WORKDIR /src/src/Web
ENV PUBLIC_API_URL=http://localhost:1612 PUBLIC_WEBSOCKET_RECONNECT_ATTEMPTS=5 PUBLIC_WEBSOCKET_RECONNECT_DELAY=1000
ENV PUBLIC_WEBSOCKET_MAX_RECONNECT_DELAY=30000 PUBLIC_WEBSOCKET_PING_TIMEOUT=15000 PUBLIC_WEBSOCKET_PING_INTERVAL=20000
RUN pnpm --filter @nocturne/bot run build && pnpm --filter @nocturne/app run build
RUN mkdir -p /out/web/packages/app /out/web/packages/bridge \
    && cp package.json pnpm-lock.yaml pnpm-workspace.yaml /out/web/ \
    && cp packages/app/package.json packages/app/server.js packages/app/server-origin-warning.js /out/web/packages/app/ \
    && cp -r packages/app/build /out/web/packages/app/ \
    && cp packages/bridge/package.json /out/web/packages/bridge/ \
    && cp -r packages/bridge/dist /out/web/packages/bridge/
# Use the matching approved Daily runtime/OS; replace its application with our source build.
FROM ghcr.io/nightscout/nocturne/nocturne-api@sha256:b3d8fb948065a13a02450087b352c0030b2dd747175764fbefb9ad4e11ffc160
USER root
COPY --from=source /out/api/ /app/
COPY --from=source /src/crates/target/release/libnocturne_alerts.so /app/libnocturne_alerts.so
ARG BUILD_VERSION=0.2.6-1
ARG BUILD_ARCH=amd64
LABEL io.hass.version="${BUILD_VERSION}" io.hass.type="app" io.hass.arch="${BUILD_ARCH}" \
      org.opencontainers.image.title="Nocturne Personal Release - Home Assistant app" \
      org.opencontainers.image.source="https://github.com/smokkelaar/nocturne-home-assistant" \
      org.opencontainers.image.licenses="AGPL-3.0-only"

# API image is Ubuntu noble/glibc. Do not copy the Alpine/musl Node executable.
COPY --from=node /usr/local/ /usr/local/
RUN printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d \
    && chmod 755 /usr/sbin/policy-rc.d \
    && apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl nginx libnginx-mod-http-js python3 openssl tini \
    && install -d /usr/share/postgresql-common/pgdg /etc/postgresql-common \
    && curl --fail --silent --show-error https://www.postgresql.org/media/keys/ACCC4CF8.asc -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
    && printf 'deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt noble-pgdg main\n' > /etc/apt/sources.list.d/pgdg.list \
    && printf 'create_main_cluster = false\n' > /etc/postgresql-common/createcluster.conf \
    && apt-get update \
    && apt-get install -y --no-install-recommends postgresql-17 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --system --create-home --uid 1655 nocturne-web

# Copy built SvelteKit output; reinstall only production dependencies for glibc.
# This does not recompile the frontend or the .NET application on the HA host.
COPY --from=source /out/web/ /opt/nocturne-web/
COPY build/ /opt/nocturne-ha-build/
WORKDIR /opt/nocturne-web
RUN python3 /opt/nocturne-ha-build/prepare_web.py /opt/nocturne-web \
    && find . -type d -name node_modules -prune -exec rm -rf '{}' + \
    && npm install -g pnpm@10.13.1 \
    && pnpm install --prod --frozen-lockfile --filter @nocturne/app... \
    && chown -R nocturne-web:nocturne-web /opt/nocturne-web
# Upstream enables a global virtual store. The guarded patch disables it so no
# runtime dependency points into root's private package cache. Test as the real
# runtime user: a root-only import check cannot detect this permission failure.
USER nocturne-web
WORKDIR /opt/nocturne-web/packages/app
RUN node /opt/nocturne-ha-build/check_web.mjs \
    && test -r build/handler.js && test -r build/server/instrumentation.server.js && test -r server.js
USER root
RUN dotnet --list-runtimes && /usr/lib/postgresql/17/bin/postgres --version

COPY rootfs/ /
RUN python3 -m compileall -q /opt/nocturne-ha \
    && chmod 755 /opt/nocturne-ha/run.py \
    && nginx -t -c /opt/nocturne-ha-build/check_cookies.conf
ENV NODE_ENV=production DOTNET_ENVIRONMENT=Production ASPNETCORE_ENVIRONMENT=Production
WORKDIR /app
EXPOSE 8099 8448
ENTRYPOINT ["/usr/bin/tini", "--", "python3", "/opt/nocturne-ha/run.py"]
CMD []
