# Scaffold

This directory holds the artifacts you get after running the bundle’s **scaffold** action: config and recipes to install, upgrade, and manage the proxy bundle.

## Prerequisites

- [porter](https://porter.sh/)
- [just](https://github.com/casey/just)

## Parameters

Applied via `parameters.yaml` (Porter parameter set `xray-headless-config`):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `namespace` | `proxy-headless` | Compose project name / namespace for services |
| `ui-port` | `2113` | Port for the web UI |
| `proxy-port` | `1081` | Local SOCKS/HTTP proxy port |
| `subscription-url-newline` | path to `subscriptions.conf` | Newline-separated subscription URLs (file path) |

Edit `parameters.yaml` to change namespace or ports. The justfile keeps `subscription-url-newline` pointing at `./subscriptions.conf` when you run install/upgrade.

## Subscriptions

Put your subscription URLs in **`subscriptions.conf`**, one per line. That file is passed into the bundle so it can fetch and merge proxy lists.

## Lifecycle (just)

| Command | Description |
|---------|-------------|
| `just install` | Install the bundle (optionally `just install -v <version>`). Updates subscription path and runs `porter install`. |
| `just upgrade` | Upgrade the installed bundle; refreshes parameters and runs `porter upgrade`. |
| `just uninstall` | Remove the bundle with `porter uninstall`. |

## Managing the proxy

After install, you can query and switch the active outbound:

| Command | Description |
|---------|-------------|
| `just current` | Show current proxy configuration (active outbound, port, etc.). |
| `just list` | List available proxies from your subscriptions. |
| `just set` | Set the active proxy. Options: |
| | `-p PORT` / `--port PORT` — choose by port (direct assignment) |
| | `-n NAME` / `--name NAME` — choose by name (substring match) |
| | `-f` / `--fastest` — choose fastest proxy (default for `set` when no other option given) |

Examples:

```bash
just list
just set -f              # use fastest
just set -n germany      # use first proxy whose name contains "germany"
just set -p 11002        # use proxy on port 11002
just current
```
