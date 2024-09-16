import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiohttp import web
import json
import os
import websockets

pcs = set()
emitter_pc=None
emitter_websocket = None

async def index(request):
    content = open('index.html', 'r').read()
    return web.Response(content_type='text/html', text=content)

async def signaling(websocket, path):
    global emitter_pc, emitter_websocket
    try:
        async for message in websocket:
            params = json.loads(message)
            print(path)
            if "sdp" in params:
                offer = RTCSessionDescription(sdp=params['sdp'], type=params['type'])
                pc = RTCPeerConnection()
                pcs.add(pc)

                @pc.on("iceconnectionstatechange")
                async def on_iceconnectionstatechange():
                    if pc.iceConnectionState == "failed":
                        await pc.close()
                        pcs.discard(pc)

                if path == "/screen_offer":
                    emitter_pc = pc
                    emitter_websocket = websocket
                    print("Emisor conectado")
                else:
                    if emitter_pc:
                        for track in emitter_pc.getTransceivers():
                            pc.addTrack(track.receiver.track)
                        print("Cliente conectado")

                await pc.setRemoteDescription(offer)
                answer = await pc.createAnswer()
                await pc.setLocalDescription(answer)

                await websocket.send(json.dumps({
                    "sdp": pc.localDescription.sdp,
                    "type": pc.localDescription.type
                }))

            # Manejando reinicio del emisor
            elif "action" in params and params["action"] == "restart_emitter":
                if emitter_websocket:
                    print("Reiniciando emisor...")
                    await emitter_websocket.send(json.dumps({"action": "restart"}))    
            else:
                print("Invalid SDP format")
                
    except Exception as e:
        print(f"Error: {e}")            
       

async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

if __name__=="__main__":    
    app = web.Application()
    app.router.add_get('/', index)

    # Manejar cierre del servidor
    app.on_shutdown.append(on_shutdown)

    # Correr el servidor HTTP con aiohttp en el puerto 8080
    web_runner = web.AppRunner(app)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(web_runner.setup())
    site = web.TCPSite(web_runner, '0.0.0.0', 8081)
    loop.run_until_complete(site.start())

    # Iniciar servidor WebSocket en el puerto 8081
    start_server = websockets.serve(signaling, "0.0.0.0", 8080)
    loop.run_until_complete(start_server)

    print("Servidor HTTP en http://0.0.0.0:8080")
    print("Servidor WebSocket en ws://0.0.0.0:8081")

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.run_until_complete(web_runner.cleanup())
        loop.run_until_complete(start_server.wait_closed())
        loop.close()

