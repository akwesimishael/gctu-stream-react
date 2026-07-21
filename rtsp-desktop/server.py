import socket
import threading
from random import randint
from RtpPacket import RtpPacket
from WebcamStream import WebcamStream

INIT = 0
READY = 1
PLAYING = 2

class ServerWorker:
    OK_200 = 0
    FILE_NOT_FOUND_404 = 1
    CON_ERR_500 = 2

    def __init__(self, clientInfo, on_client_connected=None):
        self.clientInfo = clientInfo
        self.state = INIT
        self.on_client_connected = on_client_connected

    def run(self):
        threading.Thread(target=self.recvRtspRequest, daemon=True).start()

    def recvRtspRequest(self):
        connSocket = self.clientInfo["rtspSocket"][0]
        while True:
            try:
                data = connSocket.recv(256)
                if not data:
                    break
                # print("\n--- Data received from client ---")
                # print(data.decode("utf-8"))
                self.processRtspRequest(data.decode("utf-8"))
            except ConnectionResetError:
                break
        
        # Cleanup when client disconnects
        if "videoStream" in self.clientInfo:
            self.clientInfo["videoStream"].close()
        if self.clientInfo.get("rtpSocket"):
            self.clientInfo["rtpSocket"].close()

    def processRtspRequest(self, data):
        request = data.split("\n")
        line1 = request[0].split(" ")
        requestType = line1[0]
        filename = line1[1]
        seqNum = request[1].split(" ")[1]

        if requestType == "SETUP":
            if self.state == INIT:
                print("Server: Processing SETUP")
                try:
                    self.clientInfo["videoStream"] = WebcamStream()
                except IOError:
                    self.replyRtsp(self.FILE_NOT_FOUND_404, seqNum)
                    return

                self.state = READY
                self.clientInfo["session"] = randint(100000, 999999)
                self.clientInfo["rtpPort"] = request[2].split(" ")[3]
                self.replyRtsp(self.OK_200, seqNum)
                
                if self.on_client_connected:
                    self.on_client_connected(self.clientInfo["rtspSocket"][1][0])

        elif requestType == "PLAY":
            if self.state == READY:
                print("Server: Processing PLAY, starting webcam stream")
                self.state = PLAYING
                self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.clientInfo["event"] = threading.Event()
                self.clientInfo["worker"] = threading.Thread(target=self.sendRtp, daemon=True)
                self.clientInfo["worker"].start()
                self.replyRtsp(self.OK_200, seqNum)

        elif requestType == "PAUSE":
            if self.state == PLAYING:
                print("Server: Processing PAUSE")
                self.state = READY
                self.clientInfo["event"].set()
                self.replyRtsp(self.OK_200, seqNum)

        elif requestType == "TEARDOWN":
            print("Server: Processing TEARDOWN")
            if "event" in self.clientInfo:
                self.clientInfo["event"].set()
            self.replyRtsp(self.OK_200, seqNum)
            if self.clientInfo.get("rtpSocket"):
                self.clientInfo["rtpSocket"].close()
            if "videoStream" in self.clientInfo:
                self.clientInfo["videoStream"].close()
            self.state = INIT

    def sendRtp(self):
        """Reads frames from webcam and sends as RTP packet."""
        while True:
            self.clientInfo["event"].wait(0.05)
            if self.clientInfo["event"].is_set():
                break

            data = self.clientInfo["videoStream"].nextFrame()
            if data is None:
                continue # Webcam might have dropped a frame, just continue

            frameNumber = self.clientInfo["videoStream"].frameNbr()
            try:
                address = self.clientInfo["rtspSocket"][1][0]
                port = int(self.clientInfo["rtpPort"])
                packet = self.makeRtp(data, frameNumber)
                self.clientInfo["rtpSocket"].sendto(packet, (address, port))
            except Exception as e:
                print("Server: Connection error, stopping stream:", e)
                break

    def makeRtp(self, payload, frameNbr):
        version = 2
        padding = 0
        extension = 0
        cc = 0
        marker = 0
        pt = 26  # MJPEG payload type
        ssrc = 0

        rtpPacket = RtpPacket()
        rtpPacket.encode(version, padding, extension, cc, frameNbr, marker, pt, ssrc, payload)
        return rtpPacket.getPacket()

    def replyRtsp(self, code, seq):
        if code == self.OK_200:
            reply = f"RTSP/1.0 200 OK\nCSeq: {seq}\nSession: {self.clientInfo.get('session', 0)}"
            self.clientInfo["rtspSocket"][0].send(reply.encode())
        elif code == self.FILE_NOT_FOUND_404:
            reply = f"RTSP/1.0 404 NOT FOUND\nCSeq: {seq}"
            self.clientInfo["rtspSocket"][0].send(reply.encode())

class RtspServer:
    def __init__(self, port, on_client_connected=None):
        self.port = port
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serverSocket.bind(("", self.port))
        self.serverSocket.listen(5)
        self.on_client_connected = on_client_connected
        self.running = False

    def start(self):
        self.running = True
        print(f"RTSP Server listening for incoming calls on port {self.port}...")
        threading.Thread(target=self._accept_loop, daemon=True).start()
        
    def _accept_loop(self):
        while self.running:
            try:
                clientSocket, clientAddr = self.serverSocket.accept()
                print("Server: Incoming call from:", clientAddr)
                clientInfo = {"rtspSocket": (clientSocket, clientAddr)}
                ServerWorker(clientInfo, self.on_client_connected).run()
            except Exception as e:
                if self.running:
                    print("Server accept error:", e)

    def stop(self):
        self.running = False
        self.serverSocket.close()
