# RTSP Video Streaming Project (Python)
**Group 5 — Marshalling and Unmarshalling of Data**

A video server and client that communicate using a simplified RTSP
(Real-Time Streaming Protocol) over TCP, with the actual video sent as RTP
packets over UDP.

---

## Files

| File | Purpose |
|---|---|
| `RtpPacket.py` | **The core of your topic.** `encode()` = marshalling, `decode()` = unmarshalling of RTP packets |
| `VideoStream.py` | Reads video frames one at a time from the video file |
| `server.py` | RTSP server: handles SETUP / PLAY / PAUSE / TEARDOWN, streams RTP packets |
| `client.py` | RTSP client with a simple GUI: buttons to control playback, displays incoming video |
| `make_test_video.py` | Generates a sample `movie.Mjpeg` test file so you can run the demo immediately |
| `movie.Mjpeg` | Sample test video (already generated for you — 150 colored frames) |

---

## Setup (one-time)

You need Python 3 with Pillow installed:

```
pip install pillow
```

(Tkinter, used for the client GUI, comes built into Python on Windows/Mac.
On Linux you may need `sudo apt install python3-tk`.)

---

## How to run the demo

**1. Open two terminal windows** (or two laptops on the same Wi-Fi).

**Terminal 1 — start the server:**
```
python server.py 5540
```

**Terminal 2 — start the client:**
```
python client.py 127.0.0.1 5540 25000 movie.Mjpeg
```
(If using two separate laptops, replace `127.0.0.1` with the server laptop's
IP address, and make sure both are on the same network.)

**3. In the client window**, click the buttons in order:
- **Setup** → connects and prepares the stream
- **Play** → starts streaming and displaying video
- **Pause** → pauses
- **Teardown** → ends the session and closes the connection

---

## How this maps to "Marshalling and Unmarshalling"

This is the part you'll explain in your presentation:

1. **RTSP messages (text):**
   - Client builds a request string like `SETUP movie.Mjpeg RTSP/1.0` → this is **marshalling** (turning a command into a transmittable format)
   - Server reads that string and splits it into method, filename, sequence number → this is **unmarshalling**

2. **RTP packets (binary, in `RtpPacket.py`):**
   - `encode()` takes separate values (version, sequence number, timestamp, the JPEG frame bytes) and packs them with Python's `struct` module into one binary blob → **marshalling**
   - `decode()` takes that binary blob received over UDP and unpacks it back into the separate fields and the original JPEG frame → **unmarshalling**

You can literally point to these two functions in `RtpPacket.py` as your live
code example during the presentation — they directly demonstrate the
concept with real working code, not just theory.

---

## If you want to stream a real video instead of the test pattern

Real videos need to be converted into the simple `movie.Mjpeg` format this
project uses (5-digit frame size + JPEG bytes, repeated). The easiest way is
to use OpenCV to extract frames from an `.mp4` and re-save them in that
format — ask if you'd like a converter script for that.

---

## Troubleshooting

- **"Address already in use"** — wait a few seconds and retry, or change the port number
- **No video appears** — make sure `movie.Mjpeg` is in the same folder you're running the client from, and that you clicked Setup before Play
- **Firewall blocking UDP** — if testing across two laptops, make sure the RTP port (25000) isn't blocked
