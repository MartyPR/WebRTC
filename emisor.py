import asyncio
import json
import aiohttp
from aiortc import RTCPeerConnection, RTCSessionDescription,RTCRtpCodecParameters
from aiortc.contrib.media import MediaPlayer
import websockets

async def set_video_parameters(sender, max_bitrate_bps, width, height):
    parameters = sender.getParameters()

    # Ajustar los parámetros de codificación del video
    if parameters.encodings:
        # Si hay configuraciones previas, ajusta el bitrate máximo
        parameters.encodings[0].maxBitrate = max_bitrate_bps
        
    else:
        # Si no hay configuraciones previas, crea una nueva con el bitrate deseado
        parameters.encodings = [{"maxBitrate": max_bitrate_bps}]
    parameters.encoding.scaleResolutionDownBy = 2.0
    # Modificar la resolución si es necesario
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
        screen = player_screen.video
        screen.kind = "video"
        screen.label = "screen"

        player_camera = MediaPlayer("video=USB2.0 PC CAMERA", format="dshow")
        camera = player_camera.video
        camera.kind = "video"
        camera.label = "camera"

        # Añadir ambas pistas al RTCPeerConnection
        screen_sender = pc.addTrack(screen)
        camera_sender = pc.addTrack(camera)

        # Ajustar los parámetros de bitrate y resolución de la captura de pantalla
        await set_video_parameters(screen_sender, max_bitrate_bps=500_000, width=1280, height=720)  # Bitrate en bps
        # Ajustar los parámetros de bitrate y resolución de la cámara
        await set_video_parameters(camera_sender, max_bitrate_bps=300_000, width=640, height=480)  # Bitrate en bps
         # Preferir el códec H.264 para video
        await set_video_codec_preference(pc)
        print("Captura de pantalla y cámara configuradas con parámetros ajustados.")
    
    except Exception as e:
        print(f"Error al configurar la captura: {e}")
        
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    pc.localDescription.sdp = pc.localDescription.sdp.replace(
        "a=mid:video\r\n",
        "a=mid:video\r\nb=AS:3000\r\n"
    )


    async with websockets.connect('ws://localhost:8000/screen_offer') as websocket:
        emitter_id = "emisor_1"  # Identificador para el segundo emisor
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