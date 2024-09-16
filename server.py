import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiohttp import web
import json
import os


pcs = set()
emitter_pc=None

async def index(request):
    content = open('index.html', 'r').read()
    return web.Response(content_type='text/html', text=content)

async def offer(request):
    global emitter_pc
    try:
        params = await request.json()
        offer = RTCSessionDescription(sdp=params['sdp'], type=params['type'])
        pc = RTCPeerConnection()
        pcs.add(pc)
        
        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            if pc.iceConnectionState == "failed":
                await pc.close()
                pcs.discard(pc)
                
        if request.rel_url.path == "/screen_offer":
            emitter_pc = pc
            print("Emisor conectado")
        else:
            if emitter_pc:
                for track in emitter_pc.getTransceivers():
                    pc.addTrack(track.receiver.track)   
                print("Cliente conectado")

        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        print(emitter_pc)
        return web.Response(content_type="application/json", text=json.dumps({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }))
        
    except:
        return web.Response(status=500, text="Error interno en el servidor")


async def on_shutdown(app):
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()

app = web.Application()
app.on_shutdown.append(on_shutdown)
app.router.add_get('/', index)
app.router.add_post('/offer', offer)
app.router.add_post('/screen_offer', offer)

web.run_app(app, port=8080)
