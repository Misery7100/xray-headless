FROM python:3.12-alpine

# hadolint ignore=DL3018
RUN apk add --no-cache ca-certificates wget
WORKDIR /app
COPY selector.py /app/selector.py
COPY startup.sh /startup.sh
RUN chmod +x /startup.sh

ENTRYPOINT ["/startup.sh"]