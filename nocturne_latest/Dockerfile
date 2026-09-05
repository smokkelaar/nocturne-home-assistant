# API and frontend are paired by upstream-latest.json and pinned by OCI digest.
FROM ghcr.io/nightscout/nocturne/nocturne-web@sha256:2e11a57c67089845867d3071e7a35cebb9b8b114072f1437c5442cb3a3ea59d8 AS web
FROM node:24.18.0-bookworm-slim@sha256:6f7b03f7c2c8e2e784dcf9295400527b9b1270fd37b7e9a7285cf83b6951452d AS node
FROM ghcr.io/nightscout/nocturne/nocturne-api@sha256:cb1c77d17d6fcd2d09a61db77e6707e9e74011d977620af1e6e91c09b7ed3cb0

USER root
ARG BUILD_VERSION=0.1.6-4
ARG BUILD_ARCH=amd64
LABEL io.hass.version="${BUILD_VERSION}" io.hass.type="app" io.hass.arch="${BUILD_ARCH}" \
      org.opencontainers.image.title="Nocturne Latest Release - Home Assistant app" \
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
COPY --from=web /app/ /opt/nocturne-web/
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
