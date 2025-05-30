from quart import Quart, request, websocket, Response
import httpx
import websockets
import yaml
import os
import logging
from hypercorn.config import Config
from hypercorn.asyncio import serve
import asyncio
import signal

app = Quart(__name__)
config = {}
config_lock = asyncio.Lock()

def load_config():
    immich_url = os.getenv('IMMICH_URL')
    if not immich_url:
        raise ValueError("IMMICH_URL muss in der .env-Datei konfiguriert sein!")
    
    return {
        'allowed_origins': os.getenv('CORS_ALLOWED_ORIGINS', '*').split(','),
        'immich_url': immich_url
    }

@app.before_serving
async def verify_config():
    try:
        load_config()
    except ValueError as e:
        app.logger.error(str(e))
        raise RuntimeError("Konfigurationsfehler") from e

@app.before_serving
async def setup():
    load_config()
    # Register config reload on SIGHUP
    loop = asyncio.get_event_loop()
    loop.add_signal_handler(signal.SIGHUP, load_config)

@app.after_request
async def add_cors_headers(response):
    origin = request.headers.get('Origin')
    
    if origin in config['cors']['allowed_origins']:
        response.headers['Access-Control-Allow-Origin'] = origin
        if config['cors']['allow_credentials']:
            response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'X-Api-Key, Authorization, Content-Type'
    return response

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
async def proxy_http(path):
    async with httpx.AsyncClient() as client:
        req = client.build_request(
            request.method,
            f"{config['immich']['url']}/{path}",
            headers={k: v for k, v in request.headers if k.lower() != 'host'},
            content=await request.get_data()
        )
        resp = await client.send(req, stream=True)
        return Response(resp.aiter_bytes(), status=resp.status_code, headers=dict(resp.headers))

@app.websocket('/<path:path>')
async def proxy_websocket(path):
    async with websockets.connect(f"{config['immich']['ws_url']}/{path}") as ws_client:
        async def forward():
            async for msg in websocket:
                await ws_client.send(msg)
        async def reverse():
            async for msg in ws_client:
                await websocket.send(msg)
        await asyncio.gather(forward(), reverse())

if __name__ == '__main__':
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    asyncio.run(serve(app, config))
