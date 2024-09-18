import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiohttp import web
import json
import os
import websockets

emitter_websocket = None
pcs = set()
emitter_pc = None
ROOT = os.path.dirname(__file__)
async def index(request):
    content = open(os.path.join(ROOT, "index.html"), "r").read()
    return web.Response(content_type="text/html", text=content)

async def signaling(websocket, path):
    global emitter_pc, emitter_websocket

    if path == "/screen_offer":
        try:
            async for message in websocket:
                params = json.loads(message)
                if "sdp" in params:
                    offer = RTCSessionDescription(sdp=params['sdp'], type=params['type'])
                    pc = RTCPeerConnection()
                    pcs.add(pc)

                    @pc.on("iceconnectionstatechange")
                    async def on_iceconnectionstatechange():
                        if pc.iceConnectionState == "failed":
                            await pc.close()
                            pcs.discard(pc)

                    emitter_pc = pc
                    emitter_websocket = websocket
                    print("Emisor conectado")

                    await pc.setRemoteDescription(offer)
                    answer = await pc.createAnswer()
                    await pc.setLocalDescription(answer)

                    await websocket.send(json.dumps({
                        "sdp": pc.localDescription.sdp,
                        "type": pc.localDescription.type
                    }))
                else:
                    print("Formato SDP inválido para el emisor")
        except Exception as e:
            print(f"Error con el emisor: {e}")
    elif path == "/viewer_offer":
        try:
            async for message in websocket:
                params = json.loads(message)
                if "sdp" in params and emitter_pc is not None:
                    offer = RTCSessionDescription(sdp=params['sdp'], type=params['type'])
                    pc = RTCPeerConnection()
                    pcs.add(pc)
                    
                    @pc.on("iceconnectionstatechange")
                    async def on_iceconnectionstatechange():
                        if pc.iceConnectionState == "failed":
                            await pc.close()
                            pcs.discard(pc)

                    for transceiver in emitter_pc.getTransceivers():
                        if transceiver.receiver and transceiver.receiver.track:
                            pc.addTrack(transceiver.receiver.track)

                    await pc.setRemoteDescription(offer)
                    answer = await pc.createAnswer()
                    await pc.setLocalDescription(answer)

                    await websocket.send(json.dumps({
                        "sdp": pc.localDescription.sdp,
                        "type": pc.localDescription.type
                    }))
                    print("Cliente conectado")
                elif "action" in params and params["action"] == "restart_emitter":
                    if emitter_websocket:
                        print("Reiniciando emisor...")
                        await emitter_websocket.send(json.dumps({"action": "restart"}))
        except Exception as e:
            print(f"Error con el cliente: {e}")

async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

if __name__=="__main__":
    app = web.Application()
    app.router.add_get('/', index)
    app.on_shutdown.append(on_shutdown)

    web_runner = web.AppRunner(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(web_runner.setup())
    site = web.TCPSite(web_runner, '0.0.0.0', 5000)
    loop.run_until_complete(site.start())

    start_server = websockets.serve(signaling, "0.0.0.0", 8000)
    loop.run_until_complete(start_server)

    print("Servidor HTTP en http://0.0.0.0:5000")
    print("Servidor WebSocket en ws://0.0.0.0:8000")

    loop.run_forever()
