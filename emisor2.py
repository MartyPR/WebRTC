import asyncio
import json
import aiohttp
from aiortc import RTCPeerConnection, RTCSessionDescription,RTCRtpCodecParameters
from aiortc.contrib.media import MediaPlayer
import websockets


async def set_video_parameters(sender, max_bitrate_bps, width, height):
    parameters = sender.getParameters()

    # Verifica si el campo encodings está definido en parameters
    if not parameters.encodings:
        parameters.encodings = [{}]

    # Ajustar el bitrate máximo
    parameters.encodings[0]["maxBitrate"] = max_bitrate_bps
    
    # Escalar la resolución si es necesario
    if "scaleResolutionDownBy" in parameters.encodings[0]:
        parameters.encodings[0]["scaleResolutionDownBy"] = 2.0

    # Cambiar la resolución manualmente en la pista (si es posible)
    if sender.track:
        sender.track._width = width
        sender.track._height = height

    # Aplicar los nuevos parámetros
    await sender.setParameters(parameters)
    
async def set_video_codec_preference(pc):
    # Prefer H264 codec
    for transceiver in pc.getTransceivers():
        if transceiver.kind == "video":
            preferred_codecs = [
                RTCRtpCodecParameters(
                    mimeType="video/H264",
                    clockRate=90000,
                )
            ]
            transceiver.setCodecPreferences(preferred_codecs)


async def main():
    pc = RTCPeerConnection()
    try:
        # Crear dos MediaPlayer, uno para la pantalla y otro para la cámara
        player_screen = MediaPlayer("desktop", format="gdigrab")
        screen=player_screen.video
        screen.kind="video"
        screen.label="screen"
        
        player_camera = MediaPlayer("desktop", format="gdigrab", options={"framerate": "30", "video_size":"640x360"})  # Cambia el nombre de la cámara según tu sistema
        camera=player_camera.video
        camera.kind="video"
        camera.label="webcam"
        # Añadir ambas pistas al RTCPeerConnection
        screen_sender = pc.addTrack(screen)
        camera_sender = pc.addTrack(camera)
        

    except Exception as e:
        print(f"Error al configurar la captura: {e}")
    
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    pc.localDescription.sdp = pc.localDescription.sdp.replace(
        "a=mid:video\r\n",
        "a=mid:video\r\nb=AS:2000\r\n"
    )


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