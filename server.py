import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiohttp import web
import json
import socket

pcs = set()

async def index(request):
    content = open('index.html', 'r').read()
    return web.Response(content_type='text/html', text=content)

async def offer(request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params['sdp'], type=params['type'])

    pc = RTCPeerConnection()
    pcs.add(pc)

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        if pc.iceConnectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    # Comunicación con el emisor
    player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    player_socket.connect(('localhost', 9999))  # Conecta al emisor

    pc.addTransceiver('video', direction='recvonly')

    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    # Enviar la SDP al emisor para la configuración del WebRTC
    sdp_message = {
        'sdp': pc.localDescription.sdp,
        'type': pc.localDescription.type
    }
    player_socket.sendall(json.dumps(sdp_message).encode('utf-8'))
    player_socket.close()

    return web.Response(
        content_type="application/json",
        text=json.dumps(
            {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        ),
    )

async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

app = web.Application()
app.on_shutdown.append(on_shutdown)
app.router.add_get('/', index)
app.router.add_post('/offer', offer)

web.run_app(app, port=8080)
