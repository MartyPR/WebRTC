import asyncio
import aiohttp
import cv2
import numpy as np
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer, MediaStreamTrack

class VideoTrack(MediaStreamTrack):
    def __init__(self):
        super().__init__()
        self.frame = None

    async def recv(self):
        return self.frame

async def offer(request):
    pc = RTCPeerConnection()

    # Añadir el track de video
    video_track = VideoTrack()
    pc.addTrack(video_track)

    offer = await request.json()
    offer = RTCSessionDescription(sdp=offer['sdp'], type=offer['type'])
    await pc.setRemoteDescription(offer)

    # Crear y enviar respuesta
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        'sdp': pc.localDescription.sdp,
        'type': pc.localDescription.type
    })

async def show_video(track):
    while True:
        frame = await track.recv()
        if frame:
            img = np.asarray(frame)
            cv2.imshow('Received Video', img)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    cv2.destroyAllWindows()

async def main():
    app = web.Application()
    app.router.add_post('/offer', offer)

    # Iniciar servidor
    server = web.run_app(app, port=8000)

    # Establecer conexión
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:8000/offer', json={}) as response:
            answer = await response.json()

    # Mostrar video
    await show_video(video_track)

if __name__ == '__main__':
    asyncio.run(main())
