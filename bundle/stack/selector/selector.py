import json
import os
import socket
import sys
import urllib.error
import urllib.request

# ----------------------- #

XRAY_API = os.environ.get("XRAY_API", "http://127.0.0.1:2112")
HAPROXY_SOCKET = os.environ.get("HAPROXY_SOCKET", "/var/run/haproxy.sock")

BACKEND = "b_socks"
SERVER = "s1"

# ....................... #


def http_get_json(url: str) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise SystemExit(
            f"HTTP error {e.code} for {url}: {e.read().decode('utf-8', 'ignore')}"
        )
    except Exception as e:
        raise SystemExit(f"Failed to GET {url}: {e}")


# ....................... #


def haproxy_cmd(cmd: str) -> str:
    # runtime socket: send command + '\n', read response
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect(HAPROXY_SOCKET)
    s.sendall((cmd.strip() + "\n").encode("utf-8"))
    s.shutdown(socket.SHUT_WR)
    data = s.recv(65535)
    s.close()
    return data.decode("utf-8", "ignore").strip()


# ....................... #


def list_proxies():
    data = http_get_json(f"{XRAY_API}/api/v1/proxies")
    if not data.get("success"):
        raise SystemExit(f"API error: {data}")
    proxies = data["data"]

    rows = []
    for p in proxies:
        rows.append(
            {
                "port": str(p.get("proxyPort", "")),
                "lat": str(p.get("latencyMs", "")),
                "st": "UP" if p.get("online") else "DOWN",
                "name": (p.get("name") or "").strip(),
            }
        )

    headers = ["PORT", "LAT(ms)", "ST", "NAME"]

    # widths
    w_port = (
        max(len(headers[0]), *(len(r["port"]) for r in rows))
        if rows
        else len(headers[0])
    )
    w_lat = (
        max(len(headers[1]), *(len(r["lat"]) for r in rows))
        if rows
        else len(headers[1])
    )
    w_st = (
        max(len(headers[2]), *(len(r["st"]) for r in rows)) if rows else len(headers[2])
    )
    w_name = (
        max(len(headers[3]), *(len(r["name"]) for r in rows))
        if rows
        else len(headers[3])
    )

    fmt = f"{{:<{w_port}}}  {{:>{w_lat}}}  {{:<{w_st}}}  {{:<{w_name}}}"

    print(fmt.format(*headers))
    print(fmt.format("-" * w_port, "-" * w_lat, "-" * w_st, "-" * w_name))

    for r in rows:
        print(fmt.format(r["port"], r["lat"], r["st"], r["name"]))


# ....................... #


def choose_best(proxies, name_contains: str | None):
    # filter online first; if none online, fallback to all
    def matches(p):
        if name_contains is None:
            return True
        n = (p.get("name") or "").lower()
        return name_contains.lower() in n

    filtered = [p for p in proxies if matches(p)]
    if not filtered:
        raise SystemExit(f"No proxies match: {name_contains!r}")

    online = [p for p in filtered if p.get("online") is True]
    candidates = online if online else filtered

    # prefer those with numeric latency
    def latency_key(p):
        lat = p.get("latencyMs")
        if isinstance(lat, (int, float)):
            return float(lat)
        return float("inf")

    best = sorted(candidates, key=latency_key)[0]
    if best.get("proxyPort") is None:
        raise SystemExit(f"Chosen proxy has no proxyPort: {best}")
    return best


# ....................... #


def set_backend_port(port: int):
    resp = haproxy_cmd(f"set server {BACKEND}/{SERVER} addr 127.0.0.1 port {port}")
    haproxy_cmd(f"set server {BACKEND}/{SERVER} state ready")

    print(f"HAProxy backend now -> 127.0.0.1:{port}")

    if resp:
        print(resp)


# ....................... #


def cmd_set_port(args):
    if len(args) != 1:
        raise SystemExit("Usage: set-port <port>")
    port = int(args[0])
    set_backend_port(port)


# ....................... #


def cmd_set_name(args):
    if len(args) < 1:
        raise SystemExit('Usage: set-name "<substring>"')
    needle = " ".join(args).strip()
    data = http_get_json(f"{XRAY_API}/api/v1/proxies")
    proxies = data["data"]
    best = choose_best(proxies, needle)
    print(
        f"Selected by name={needle!r}: {best.get('name')} (lat={best.get('latencyMs')}ms, port={best.get('proxyPort')})"
    )
    set_backend_port(int(best["proxyPort"]))


# ....................... #


def cmd_fastest(_args):
    data = http_get_json(f"{XRAY_API}/api/v1/proxies")
    proxies = data["data"]
    best = choose_best(proxies, None)
    print(
        f"Selected fastest: {best.get('name')} (lat={best.get('latencyMs')}ms, port={best.get('proxyPort')})"
    )
    set_backend_port(int(best["proxyPort"]))


# ....................... #


def cmd_current(_args):
    out = haproxy_cmd(f"show servers state {BACKEND}")

    lines = [li.strip() for li in out.splitlines() if li.strip()]

    header_line = next((li for li in lines if li.startswith("#")), None)

    if not header_line:
        print("Cannot parse HAProxy output")
        print(out)
        return

    headers = header_line.lstrip("# ").split()

    idx = lines.index(header_line)
    values_line = lines[idx + 1]

    values = values_line.split()

    data = dict(zip(headers, values))

    addr = data.get("srv_addr", "?")
    port = data.get("srv_port", "?")

    state_code = data.get("srv_admin_state", "?")

    state_map = {
        "0": "ready",
        "1": "drain",
        "2": "maint",
    }

    state = state_map.get(state_code, state_code)

    print("Current backend:")
    print(f"  server: {BACKEND}/{SERVER}")
    print(f"  addr:   {addr}:{port}")
    print(f"  state:  {state}")

    try:
        data = http_get_json(f"{XRAY_API}/api/v1/proxies")

        if data.get("success"):

            proxies = data["data"]

            match = next((p for p in proxies if str(p.get("proxyPort")) == port), None)

            if match:

                name = match.get("name", "?")
                latency = match.get("latencyMs", "?")
                online = match.get("online")

                status = "UP" if online else "DOWN"

                print()
                print("Profile:")
                print(f"  name:    {name}")
                print(f"  port:    {port}")
                print(f"  latency: {latency} ms")
                print(f"  status:  {status}")

            else:
                print()
                print(f"No matching profile for port {port}")

    except Exception as e:

        print()
        print(f"Failed to query xray-checker API: {e}")


# ....................... #


def main():
    if len(sys.argv) < 2:
        print(
            "Commands: list | set-port <port> | set-name <substring> | fastest | current"
        )
        sys.exit(2)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "list":
        list_proxies()

    elif cmd == "set-port":
        cmd_set_port(args)

    elif cmd == "set-name":
        cmd_set_name(args)

    elif cmd == "fastest":
        cmd_fastest(args)

    elif cmd == "current":
        cmd_current(args)

    else:
        raise SystemExit(f"Unknown command: {cmd}")


# ----------------------- #

if __name__ == "__main__":
    main()
