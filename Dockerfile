FROM ghcr.io/astral-sh/uv:python3.11-trixie

WORKDIR /app

COPY docker-entrypoint /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint
ENTRYPOINT ["/usr/local/bin/docker-entrypoint"]
