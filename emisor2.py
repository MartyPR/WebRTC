import asyncio
import json
import aiohttp
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer
import websockets

async def main():
    pc = RTCPeerConnection()
    try:
        # Crear dos MediaPlayer, uno para la pantalla y otro para la cámara
        player_screen = MediaPlayer("desktop", format="gdigrab", options={"framerate": "30"})
        screen=player_screen.video
        screen.kind="video"
        screen.label="asd"
        player_camera = MediaPlayer("desktop", format="gdigrab", options={"framerate": "30", "video_size":"640x360"})  # Cambia el nombre de la cámara según tu sistema
        camera=player_camera.video
        camera.kind="video"
        camera.label="asd"
        # Añadir ambas pistas al RTCPeerConnection
        pc.addTrack(screen)
        pc.addTrack(camera)
        print("Captura de pantalla y cámara")
    
    except Exception as e:
        print(f"Error al configurar la captura: {e}")
    
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    async with websockets.connect('ws://localhost:8000/screen_offer') as websocket:
        emitter_id = "emisor_2"  # Identificador para el segundo emisor
        await websocket.send(json.dumps({
            "sdp": pc.localDescription.sdp,
            "type": pc.localDescription.type,
            "emitter_id": emitter_id
        }))
        while True:
            response = await websocket.recv()
            answer = json.loads(response)

            if "sdp" in answer:
                await pc.setRemoteDescription(RTCSessionDescription(sdp=answer['sdp'], type=answer['type']))
            elif "action" in answer and answer["action"] == "restart":
                print("Reiniciando emisor...")
                await pc.close()
                return await main()

if __name__ == '__main__':
    asyncio.run(main())