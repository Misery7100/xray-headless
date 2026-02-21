# Xray :: Headless

Porter bundle for running [xray](https://github.com/XTLS/Xray-core) proxy headless: subscribe to proxy lists, choose an outbound, expose a local SOCKS/HTTP proxy.

## Quick start

1. Create a target directory for the scaffold files, update permissions to allow the bundle to write to it:

   ```bash
   mkdir -p xray-headless
   chmod -R 777 xray-headless
   ```

2. Run the **scaffold** action so the bundle extracts the necessary files into the target directory. From that directory you can then install, upgrade, and manage the proxy:

   ```bash
   porter invoke --action scaffold \
     --reference ghcr.io/misery7100/xray-headless:latest \
     --mount-host-volume "$(pwd)/xray-headless:/out:rw"
   ```

3. `cd` into the target directory and follow [README.md](bundle/scaffold/README.md) to configure subscriptions and run install/upgrade/management.
