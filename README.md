# Immich CORS Proxy

A Proxy-Server to handle OPTIONS Requests to use the Immich API in JavaScript ApplicationsA Docker container that acts as a CORS proxy and WebSocket gateway for Immich.

**Features:**

- Environment-based configuration via .env file
- Automatic WebSocket support
- Strict configuration validation (fails if required values are missing)
- Warnings for insecure CORS configurations (e.g. `*` origin)

## Prerequisites

- Docker and Docker Compose
- Git (optional, for cloning the repository)

## Installation

### Clone the Repository

```bash
git clone https://github.com/keineantwort/immich-cors-proxy.git
cd immich-cors-proxy
```

### Configure the proxy

#### the `.env` file

```bash
cp .env.example .env
nano .env
```

**Sample `.env` file:**

```text
# Allowed CORS origins (comma-separated)
CORS_ALLOWED_ORIGINS=https://ha.example.com,https://wallpanel.example.com

# Immich API URL (required)
IMMICH_URL=http://immich-server:2283
```

**Note:**
`IMMICH_URL` is required. The container will fail to start if this value is missing.

#### the Immich `docker-compose.yml`

```yaml
version: '3.8'

services:
  immich-server:
    #... (immich-server config)

  cors-proxy:
    build: ./immich-cors-proxy
    env_file: ./immich-cors-proxy/.env
    ports:
      - "5000:5000"
    restart: unless-stopped
    depends_on:
      - immich-server

  db:
    image: postgres:15
    # ... (rest of Immich's default DB config)

  redis:
    image: redis:7
    # ... (rest of Immich's default Redis config)

```

### Install Dependencies

#### For Local Development

```bash
pip install -r requirements.txt
```

#### For Docker (automatic)

```bash
docker compose build cors-proxy
```

### Start the Containers

```bash
docker compose up -d
```

## Proxy Configuration

To use the CORS Proxy for Immich, you need to redirect all requests to `https://<your-immich-url>/api` to the CORS Proxy `http://<immich-url>:5000`.

_If you want to document other Proxies, feel free to place a PullRequest._

### Zoraxy

#### Proxy-Host for Immich (_if needed_)

- **Domain:** `immich.home.msc.wtf`
- **Target:** `http://immich-url:2283`
- **Custom Header:**  `Access-Control-Allow-Origin: (leer lassen – wird vom Dummy-Server gesetzt)`

#### Add a Virtual Directory

- Under the selected host, find the Virtual Directories section.
- Click Add Virtual Directory.
- Path: `/api`
- Target: `http://cors-proxy:5000` (or your Docker service name and port)
- Enable WebSocket Support: Check this option if your backend supports WebSockets.
- _Optional:_ Add custom headers if needed, but our CORS proxy already handles CORS headers.

## Usage

### Proxy Host Configuration (Zoraxy/Nginx Proxy Manager)

|||
|------------|-----------------------|
| **Domain** | immich.yourdomain.com |
| **Target** | <http://cors-proxy:5000> |
| **WebSocket support** | Enable in proxy settings |

## Testing

### Check CORS Headers

```bash
curl -X OPTIONS http://immich.yourdomain.com/api -I
```

**Expected output:**

```text
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: https://<your configured host>
Access-Control-Allow-Methods: GET, PUT, POST, DELETE, OPTIONS
...
```

### Test WebSockets

In a browser console like Chrome:

```javascript
const ws = new WebSocket('wss://immich.yourdomain.com/api/notifications');
ws.onmessage = console.log;
```

## Updates

```bash
git pull origin main
docker compose down && docker compose up -d --build
```

## Troubleshooting

- **"IMMICH_URL must be configured!"**
  - Make sure the .env file exists and contains `IMMICH_URL=your-value`.
  - No spaces around the equals sign: `IMMICH_URL=value`
- **Python dependencies missing**
  - Run `pip install -r requirements.txt` (local) or `docker compose build` (Docker)
- Logs:
  - `docker compose logs cors-proxy --tail=100`
