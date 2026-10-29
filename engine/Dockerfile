# Engine base image. Built rarely; the app Dockerfile starts FROM this.
# Rebuild when vendor/, csrc/, or scripts/build-native.sh changes.
FROM debian:bookworm-slim AS native

RUN apt-get update \
    && apt-get install -y --no-install-recommends clang \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY vendor /src/vendor
COPY csrc /src/csrc
COPY scripts /src/scripts
ENV CXX=clang++
RUN bash scripts/build-native.sh

FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends libstdc++6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=native /src/build/libclothoidlab.so /app/build/libclothoidlab.so

ENV HOST=0.0.0.0 \
    PORT=8080 \
    PYTHONUNBUFFERED=1

EXPOSE 8080
CMD ["python", "web/server.py"]
