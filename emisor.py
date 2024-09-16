import asyncio
import json
import aiohttp
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer

async def main():
    # Crear conexión peer-to-peer
    pc = RTCPeerConnection()

    # Captura de pantalla usando MediaPlayer
    player = MediaPlayer("desktop", format="gdigrab", options={"framerate": "5"})
    pc.addTrack(player.video)

    # Crear oferta
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    # Enviar la oferta al servidor remoto (cambiar URL por la IP/host de tu servidor)
    async with aiohttp.ClientSession() as session:
        async with session.post('http://localhost:8080/screen_offer', json={
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }) as response:
            if response.status != 200:
                raise Exception(f"Error en el servidor: {response.status}")
            data = await response.json()

    # Configurar la respuesta del servidor remoto
    answer = RTCSessionDescription(sdp=data['sdp'], type=data['type'])
    await pc.setRemoteDescription(answer)

    # Mantener la conexión abierta
    await asyncio.sleep(3600)  # Mantener activo por 1 hora (ajustable)

if __name__ == '__main__':
    asyncio.run(main())
