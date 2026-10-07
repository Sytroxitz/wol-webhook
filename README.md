# WoL Webhook + Custom GPT

A tiny Wake-on-LAN webhook (Docker, Python standard library only) plus an OpenAPI spec so a Custom GPT can wake a device on your home network.

## 1. PC prerequisites
- Enable WoL in BIOS/UEFI ("Wake on LAN" / "Power on by PCIe")
- Windows: Device Manager → network adapter → Power Management → allow "Magic Packet"; disable Fast Startup
- Use a wired LAN connection (Wi-Fi usually doesn't work)
- Note the MAC address (`ipconfig /all` or `ip link`)

## 2. Start the webhook (homelab / Raspberry Pi on the same LAN)
```bash
cp .env.example .env      # set API_KEY (openssl rand -hex 32), MAC, and optionally BROADCAST
docker compose up -d --build
curl -H "Authorization: Bearer <API_KEY>" http://localhost:8080/devices
curl -X POST -H "Authorization: Bearer <API_KEY>" http://localhost:8080/wake/pc
```
Note: `network_mode: host` only works on Linux.

## 3. Make it reachable from outside (HTTPS required for GPT Actions)
Recommended: a Cloudflare Tunnel pointing to `http://localhost:8080`, e.g. `wol.your-domain.com`.
Alternatives: Tailscale Funnel or a reverse proxy (Traefik/Caddy) with Let's Encrypt.

## 4. Custom GPT
1. ChatGPT → Create a GPT → Configure → Add action
2. Paste the contents of `openapi.yaml` and adjust `servers.url`
3. Authentication: API key → auth type "Bearer" → your `API_KEY`
4. Example instruction: "When the user wants to start the PC, call wakeDevice with device=pc."

## Security
- Only devices listed in `DEVICES` can be woken (no free-form MAC input)
- Keep the key long and random; rotate it if you suspect a leak
- Optionally put Cloudflare Access / rate limiting in front
