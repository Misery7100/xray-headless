FROM python:3.12-alpine

# hadolint ignore=DL3018
RUN apk add --no-cache ca-certificates
WORKDIR /app
COPY selector.py /app/selector.py