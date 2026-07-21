"""
RtpPacket.py

This file is the heart of your presentation topic: MARSHALLING and
UNMARSHALLING of data.

- encode()  -> MARSHALLING: takes plain Python values (sequence number,
               timestamp, a chunk of video data, etc.) and packs them into
               a single byte stream that can travel over the network.
- decode()  -> UNMARSHALLING: takes the raw bytes received from the network
               and unpacks them back into separate, usable Python values.

The RTP header here is a simplified 12-byte version of the real RTP header
format (RFC 3550), enough to demonstrate the concept clearly.
"""

import struct
import time

HEADER_SIZE = 12


class RtpPacket:
    def __init__(self):
        self.header = bytearray(HEADER_SIZE)
        self.payload = b""

    # ---------------- MARSHALLING ----------------
    def encode(self, version, padding, extension, cc, seqnum, marker, pt, ssrc, payload):
        """
        Pack RTP header fields + the actual video frame bytes into one
        byte stream ready to be sent over UDP.
        """
        timestamp = int(time.time())

        byte0 = (version << 6) | (padding << 5) | (extension << 4) | cc
        byte1 = (marker << 7) | pt

        # '!BBHII' = network byte order: 2 bytes, 1 short, 2 ints
        header = struct.pack(
            "!BBHII",
            byte0,
            byte1,
            seqnum & 0xFFFF,
            timestamp & 0xFFFFFFFF,
            ssrc & 0xFFFFFFFF,
        )

        self.header = header
        self.payload = payload

    def getPacket(self):
        """Returns the full marshalled packet (header + payload) as bytes."""
        return self.header + self.payload

    # ---------------- UNMARSHALLING ----------------
    def decode(self, byteStream):
        """
        Take raw bytes received from the network and unpack them back into
        separate header fields and the original payload.
        """
        self.header = bytearray(byteStream[:HEADER_SIZE])
        self.payload = byteStream[HEADER_SIZE:]

        byte0, byte1, seqnum, timestamp, ssrc = struct.unpack(
            "!BBHII", bytes(self.header)
        )

        self.version = (byte0 >> 6) & 0x03
        self.padding = (byte0 >> 5) & 0x01
        self.extension = (byte0 >> 4) & 0x01
        self.cc = byte0 & 0x0F
        self.marker = (byte1 >> 7) & 0x01
        self.payloadType = byte1 & 0x7F
        self.seqnum = seqnum
        self.timestamp = timestamp
        self.ssrc = ssrc

    def seqNum(self):
        return self.seqnum

    def timeStamp(self):
        return self.timestamp

    def getPayload(self):
        return self.payload
