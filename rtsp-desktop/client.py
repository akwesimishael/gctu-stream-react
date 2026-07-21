import socket
import threading
import time
from RtpPacket import RtpPacket

INIT = 0
READY = 1
PLAYING = 2

class RtspClient:
    def __init__(self, serverAddr, serverPort, rtpPort, on_frame_received, on_status_change):
        self.serverAddr = serverAddr
        self.serverPort = int(serverPort)
        self.rtpPort = int(rtpPort)
        self.filename = "webcam" # Dummy filename
        self.on_frame_received = on_frame_received
        self.on_status_change = on_status_change

        self.state = INIT
        self.session = 0
        self.cseq = 0
        self.frameNbr = 0
        
        self.rtspSocket = None
        self.rtpSocket = None
        self.listen_thread = None

    def connect(self):
        try:
            self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
            self.on_status_change(f"Connected to {self.serverAddr}")
            self.sendRtspRequest("SETUP")
            return True
        except Exception as e:
            self.on_status_change(f"Connection failed: {e}")
            return False

    def play(self):
        if self.state == READY:
            self.sendRtspRequest("PLAY")

    def pause(self):
        if self.state == PLAYING:
            self.sendRtspRequest("PAUSE")

    def teardown(self):
        if self.state != INIT:
            self.sendRtspRequest("TEARDOWN")
        if self.rtpSocket:
            self.rtpSocket.close()

    def sendRtspRequest(self, requestType):
        self.cseq += 1
        if requestType == "SETUP":
            request = f"SETUP {self.filename} RTSP/1.0\nCSeq: {self.cseq}\nTransport: RTP/UDP; client_port= {self.rtpPort}"
        else:
            request = f"{requestType} {self.filename} RTSP/1.0\nCSeq: {self.cseq}\nSession: {self.session}"

        try:
            self.rtspSocket.send(request.encode())
            reply = self.rtspSocket.recv(1024)
            self.parseRtspReply(reply.decode())

            if requestType == "SETUP" and self.state == INIT:
                self.state = READY
                self.openRtpPort()
                # Automatically play after setup
                self.play()
            elif requestType == "PLAY" and self.state == READY:
                self.state = PLAYING
                self.on_status_change("Call in progress...")
            elif requestType == "PAUSE" and self.state == PLAYING:
                self.state = READY
                self.on_status_change("Call paused")
            elif requestType == "TEARDOWN":
                self.state = INIT
                self.on_status_change("Call ended")
        except Exception as e:
            self.on_status_change(f"RTSP error: {e}")

    def parseRtspReply(self, data):
        lines = data.split("\n")
        statusLine = lines[0].split(" ")
        seqNum = int(lines[1].split(" ")[1])
        if seqNum == self.cseq and len(lines) > 2:
            session = int(lines[2].split(" ")[1])
            if self.session == 0:
                self.session = session
            if statusLine[1] != "200":
                print("Client: RTSP error:", data)

    def openRtpPort(self):
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.rtpSocket.settimeout(0.5)
        self.rtpSocket.bind(("", self.rtpPort))
        self.listen_thread = threading.Thread(target=self.listenRtp, daemon=True)
        self.listen_thread.start()

    def listenRtp(self):
        while True:
            if self.state != PLAYING:
                if self.state == INIT:
                    break
            try:
                data = self.rtpSocket.recv(65536)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)
                    currFrameNbr = rtpPacket.seqNum()

                    if currFrameNbr > self.frameNbr:
                        self.frameNbr = currFrameNbr
                        self.on_frame_received(rtpPacket.getPayload())
            except socket.timeout:
                continue
            except OSError:
                break
