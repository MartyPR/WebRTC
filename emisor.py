import asyncio
import json
import aiohttp
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer
import websockets

async def main():
    pc = RTCPeerConnection()
    player = MediaPlayer("desktop", format="gdigrab", options={"framerate": "25"})
    pc.addTrack(player.video)

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    async with websockets.connect('ws://localhost:8080/screen_offer') as websocket:
        await websocket.send(json.dumps({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type
        }))
        # Bucle para escuchar reinicio o respuesta del servidor
        while True:
            response = await websocket.recv()
            answer = json.loads(response)

            if "sdp" in answer:
                await pc.setRemoteDescription(RTCSessionDescription(sdp=answer['sdp'], type=answer['type']))
            elif "action" in answer and answer["action"] == "restart":
                print("Reiniciando emisor...")
                # Reiniciar la conexión P2P
                await pc.close()
                return await main()

if __name__ == '__main__':
    asyncio.run(main())
