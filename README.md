# Proyecto de WebRTC para Compartir Pantalla y Cámara
Este proyecto implementa una aplicación de WebRTC (Web Real-Time Communication) que permite compartir tanto la pantalla como la cámara de un emisor a uno o más clientes de forma simultánea. El proyecto está construido sobre tecnologías como Python, aiohttp para el servidor HTTP, WebSockets para la comunicación de señales, y aiortc para el manejo de las conexiones WebRTC.

## Componentes principales:
### Servidor Web (HTTP y WebSocket):

- El servidor está escrito en Python utilizando aiohttp para manejar las conexiones HTTP y websockets para las señales necesarias para establecer las conexiones WebRTC entre el emisor y los clientes.
- El servidor sirve una página HTML que contiene un reproductor de video donde los clientes pueden ver las transmisiones de pantalla y cámara.
- Las señales para establecer las conexiones WebRTC (ofertas y respuestas SDP) se manejan a través de WebSockets.
### Emisor:

- El emisor es responsable de capturar dos fuentes de video: la pantalla y la cámara.
- Utiliza la biblioteca aiortc para establecer una conexión WebRTC con el servidor y compartir ambas fuentes de video.
Se utilizan diferentes métodos de captura dependiendo de la fuente:
- Captura de pantalla: Se usa MediaPlayer con formatos como gdigrab o x11grab, dependiendo del sistema operativo, para capturar el contenido de la pantalla.
- Captura de cámara: También se usa MediaPlayer, pero esta vez con la entrada de la cámara (por ejemplo, /dev/video0 en Linux).
El emisor envía estas dos fuentes de video al servidor mediante una conexión Peer-to-Peer (P2P) que el servidor negocia con los clientes.
### Cliente:

- El cliente accede a la interfaz HTML proporcionada por el servidor para ver la transmisión en vivo tanto de la pantalla como de la cámara del emisor.
- Utilizando WebRTC, el cliente se conecta al servidor y recibe dos flujos de video que se muestran en dos elementos <video> separados en la página.
- La comunicación entre el cliente y el servidor para las señales de WebRTC se realiza a través de WebSockets.
### Negociación de Pistas (Tracks):

-Para gestionar las dos fuentes de video, el servidor utiliza transceivers, que son objetos en WebRTC que permiten recibir múltiples flujos multimedia (tracks) dentro de una misma conexión.
-El cliente se asegura de recibir correctamente ambas pistas y las asigna a dos elementos de video diferentes (uno para la pantalla y otro para la cámara).

## Flujo de Trabajo:
1. El emisor se conecta al servidor mediante WebSockets, y envía una oferta SDP con la descripción de sus dos flujos de video.
2. El servidor recibe la oferta, negocia las pistas y reenvía la descripción de la sesión a los clientes conectados.
3. Los clientes aceptan la oferta, responden con una respuesta SDP y comienzan a recibir las transmisiones de video (pantalla y cámara).
4. Los flujos de video se asignan a los elementos de video en el cliente, mostrando la pantalla y la cámara simultáneamente.
