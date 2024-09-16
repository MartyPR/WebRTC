import socket
import json
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer

async def iniciar_captura():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 9999))
    server_socket.listen(1)

    while True:
        connection, _ = server_socket.accept()
        try:
            data = connection.recv(4096)
            if data:
                try:
                    sdp_message = json.loads(data.decode('utf-8'))
                    await manejar_sdp(sdp_message)
                except json.JSONDecodeError:
                    print("Error al decodificar JSON")
        except Exception as e:
            print(f"Error en la conexión: {e}")
        finally:
            connection.close()

async def manejar_sdp(sdp_message):
    pc = RTCPeerConnection()

    @pc.on("iceconnectionstatechange")
    async def on_iceconnectionstatechange():
        if pc.iceConnectionState == "failed":
            await pc.close()

    # Captura de pantalla usando MediaPlayer
    player = MediaPlayer("desktop", format="gdigrab", options={"framerate": "30"})
    pc.addTrack(player.video)

    offer = RTCSessionDescription(sdp=sdp_message['sdp'], type=sdp_message['type'])

    # Asegúrate de que la conexión esté en un estado adecuado para manejar la oferta
    if pc.signalingState == 'stable':
        print("La conexión ya está estable, asegurando que la oferta se maneje correctamente.")
        return

    # Configura la oferta y responde
    if pc.signalingState == 'have-remote-offer':
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
    else:
        print("Estado de señalización inesperado:", pc.signalingState)

    print("Emisor listo y capturando pantalla...")

if __name__ == "__main__":
    asyncio.run(iniciar_captura())
