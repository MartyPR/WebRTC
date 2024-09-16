import asyncio
import cv2
import numpy as np
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.signaling import BYE
import aiohttp

# Track para capturar la pantalla y enviar los frames
class ScreenTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        # Usamos cv2 para capturar la pantalla
        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) # Modifica este método si usas un SO diferente.

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        ret, frame = self.cap.read()
        if not ret:
            raise Exception("Error capturando la pantalla")

        # Convertir el frame a formato RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Crear frame de video
        frame = np.ascontiguousarray(frame_rgb)
        return frame

async def send_offer(session):
    pc = RTCPeerConnection()

    @pc.on("icegatheringstatechange")
    def on_ice_gathering_state_change(event):
        print(f"ICE gathering state changed: {pc.iceGatheringState}")

    # Añadir la captura de pantalla como pista de video
    pc.addTrack(ScreenTrack())

    # Generar una oferta y enviarla al servidor
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    async with session.post("http://localhost:8080/offer", json={
        'sdp': pc.localDescription.sdp,
        'type': pc.localDescription.type
    }) as resp:
        answer = await resp.json()
        await pc.setRemoteDescription(
            RTCSessionDescription(sdp=answer['sdp'], type=answer['type'])
        )

    # Mantener la conexión activa
    await BYE.wait()

async def main():
    async with aiohttp.ClientSession() as session:
        await send_offer(session)

if __name__ == "__main__":
    asyncio.run(main())
