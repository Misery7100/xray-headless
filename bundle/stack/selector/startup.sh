#!/bin/sh
set -eu

echo "Selector startup: waiting for services..."

MAX_WAIT=60
SLEEP=2
ELAPSED=0

wait_ready() {
	if ! wget -q -T 2 -O - "${XRAY_API}/health" >/dev/null 2>&1; then
		return 1
	fi

	if [ ! -S "${HAPROXY_SOCKET}" ]; then
		return 1
	fi

	return 0
}

while [ "$ELAPSED" -lt "$MAX_WAIT" ]; do
	if wait_ready; then
		echo "Services ready."
		break
	fi

	sleep "$SLEEP"
	ELAPSED=$((ELAPSED + SLEEP))
done

echo "Running initial fastest selection..."

if python /app/selector.py fastest; then
	echo "Initial selection done."
else
	echo "Initial selection failed (continuing anyway)."
fi

echo "Selector ready."

exec sleep infinity
