import cv2
import threading

class SharedWebcam:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SharedWebcam, cls).__new__(cls)
                cls._instance._init()
            return cls._instance

    def _init(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.latest_jpeg = None
        self.latest_rgb = None
        self.running = True
        self.frame_num = 0
        threading.Thread(target=self._capture_loop, daemon=True).start()

    def _capture_loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if ret:
                # Encode for RTSP Stream
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 60]
                _, encimg = cv2.imencode('.jpg', frame, encode_param)
                
                # Convert to RGB for local GUI preview
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                with self._lock:
                    self.latest_jpeg = encimg.tobytes()
                    self.latest_rgb = rgb
                    self.frame_num += 1
            cv2.waitKey(30) # ~30 fps

    def get_latest_jpeg(self):
        with self._lock:
            return self.latest_jpeg, self.frame_num
            
    def get_latest_rgb(self):
        with self._lock:
            return self.latest_rgb

    def close(self):
        self.running = False
        if self.cap:
            self.cap.release()

class WebcamStream:
    def __init__(self):
        self.shared = SharedWebcam()

    def nextFrame(self):
        """Reads a frame from the shared webcam, encoded as JPEG."""
        jpeg, num = self.shared.get_latest_jpeg()
        self.current_num = num
        return jpeg

    def frameNbr(self):
        return self.current_num
        
    def close(self):
        pass # App will close the shared webcam
