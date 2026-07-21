"""
make_test_video.py

Generates a small test video file (movie.Mjpeg) made of synthetic colored
frames with a frame number drawn on each one. This lets you test the
server/client right away without needing a real video file.

The file format is simple:
    [5-digit frame size][JPEG bytes][5-digit frame size][JPEG bytes] ...

Run:
    python make_test_video.py
"""

import io
from PIL import Image, ImageDraw

NUM_FRAMES = 150
WIDTH, HEIGHT = 320, 240
COLORS = [(220, 60, 60), (60, 140, 220), (60, 200, 100), (230, 200, 60)]


def main():
    with open("movie.Mjpeg", "wb") as f:
        for i in range(NUM_FRAMES):
            color = COLORS[i % len(COLORS)]
            img = Image.new("RGB", (WIDTH, HEIGHT), color)
            draw = ImageDraw.Draw(img)
            draw.text((20, 100), f"Frame {i + 1}/{NUM_FRAMES}", fill=(255, 255, 255))

            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            jpegBytes = buf.getvalue()

            frameSize = str(len(jpegBytes)).zfill(5).encode()
            f.write(frameSize)
            f.write(jpegBytes)

    print(f"Created movie.Mjpeg with {NUM_FRAMES} frames.")


if __name__ == "__main__":
    main()
