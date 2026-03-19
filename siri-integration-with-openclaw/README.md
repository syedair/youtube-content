# How I Gave Siri a Brain Upgrade with OpenClaw

Siri can now talk to your own AI — no third-party cloud services, no data leaving your network.

This guide shows how to connect Apple's Siri to any large language model using [OpenClaw](https://github.com/syedair/openclaw), an open-source AI gateway. Using Siri Shortcuts' "Get Contents of URL" action, we send voice prompts directly to a self-hosted AI and get spoken responses back.

📱 **Download the Siri Shortcut:** https://www.icloud.com/shortcuts/c613072de50040908bc6e7d04c81fe96

## What's Covered

- Configuring OpenClaw for HTTP access with token auth
- Building the Siri Shortcut step by step
- Session persistence (Siri remembers context!)
- Custom voice prefixes for AI responses
- Bonus: Accessing your AI from anywhere with Cloudflare Tunnel
- Securing it all with Cloudflare Access + service tokens

## OpenClaw Gateway Config

Add the following to your `openclaw.json`:

```json
{
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "lan",
    "auth": {
      "mode": "token",
      "token": "REPLACE_WITH_YOUR_SECRET_TOKEN"
    },
    "http": {
      "endpoints": {
        "responses": {
          "enabled": true
        }
      }
    }
  }
}
```

**Key settings:**

- `bind: "lan"` — exposes the gateway on your local network so Siri can reach it
- `auth.mode: "token"` — secures the endpoint with a bearer token
- `http.endpoints.responses.enabled: true` — enables the HTTP response endpoint that Siri Shortcuts calls

## Links

- [OpenClaw](https://github.com/syedair/openclaw)
- [Cloudflare Tunnel docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)

Your voice. Your server. Your AI.
