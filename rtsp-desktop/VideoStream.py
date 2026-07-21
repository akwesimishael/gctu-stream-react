"""
VideoStream.py

Reads video frames one at a time from a simple custom video file format:

    [5-digit frame size][JPEG frame bytes][5-digit frame size][JPEG frame bytes]...

This keeps the project simple -- no need for a full video codec library.
Use make_test_video.py to generate a sample file in this format.
"""


class VideoStream:
    def __init__(self, filename):
        self.filename = filename
        try:
            self.file = open(filename, "rb")
        except FileNotFoundError:
            raise IOError(f"Cannot open video file: {filename}")
        self.frameNum = 0

    def nextFrame(self):
        """Reads and returns the next frame's raw JPEG bytes, or None at EOF."""
        sizeStr = self.file.read(5)
        if not sizeStr:
            return None
        frameLength = int(sizeStr)
        data = self.file.read(frameLength)
        self.frameNum += 1
        return data

    def frameNbr(self):
        return self.frameNum
