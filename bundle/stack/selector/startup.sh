#!/bin/sh
set -eu

echo "Selector startup: waiting for services..."

MAX_WAIT="${MAX_WAIT:-300}"
SLEEP="${SLEEP:-2}"
ELAPSED=0

XRAY_API="${XRAY_API:-http://127.0.0.1:2112}"
HAPROXY_SOCKET="${HAPROXY_SOCKET:-/var/run/haproxy.sock}"

wait_xray() {
	wget -q -T 2 -O /dev/null "${XRAY_API}/api/v1/proxies" >/dev/null 2>&1
}

wait_haproxy_socket_connect() {
	python - <<'PY' >/dev/null 2>&1
import os, socket, sys
p = os.environ.get("HAPROXY_SOCKET", "/var/run/haproxy.sock")
if not os.path.exists(p):
    sys.exit(1)
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(1)
try:
    s.connect(p)
except Exception:
    sys.exit(1)
finally:
    try: s.close()
    except: pass
sys.exit(0)
PY
}

while [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
	if wait_xray && wait_haproxy_socket_connect; then
		echo "Services ready."
		break
	fi

	sleep "$SLEEP"
	ELAPSED=$((ELAPSED + SLEEP))
done

if [ "$ELAPSED" -ge "$MAX_WAIT" ]; then
	echo "Timeout waiting for XRAY_API and HAProxy socket after ${MAX_WAIT}s"
	exit 1
fi

echo "Running initial fastest selection..."
python /app/selector.py fastest
echo "Initial selection done."

echo "Selector ready."
exec sleep infinity
