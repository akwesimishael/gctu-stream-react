import customtkinter as ctk
import threading
import socket
import io
from PIL import Image, ImageTk
from server import RtspServer
from client import RtspClient
from WebcamStream import SharedWebcam

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class VideoChatApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("RTSP Video Chat")
        self.geometry("900x600")
        
        self.shared_cam = SharedWebcam()
        self.server = None
        self.client = None
        
        self.create_widgets()
        self.update_local_preview()

    def create_widgets(self):
        # Top Control Panel
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(pady=10, padx=10, fill="x")
        
        # Ports Configuration (for local testing)
        settings_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        settings_frame.pack(side="left", padx=10)
        
        ctk.CTkLabel(settings_frame, text="My RTSP Port:").grid(row=0, column=0, padx=5)
        self.my_rtsp_port_entry = ctk.CTkEntry(settings_frame, width=60)
        self.my_rtsp_port_entry.insert(0, "5540")
        self.my_rtsp_port_entry.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(settings_frame, text="My RTP Port:").grid(row=1, column=0, padx=5)
        self.my_rtp_port_entry = ctk.CTkEntry(settings_frame, width=60)
        self.my_rtp_port_entry.insert(0, "25000")
        self.my_rtp_port_entry.grid(row=1, column=1, padx=5)
        
        self.start_server_btn = ctk.CTkButton(settings_frame, text="Start My Server", command=self.start_server, width=100)
        self.start_server_btn.grid(row=0, column=2, rowspan=2, padx=10)

        # Call Panel
        call_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        call_frame.pack(side="right", padx=10)
        
        ctk.CTkLabel(call_frame, text="Target IP:").grid(row=0, column=0, padx=5)
        self.target_ip_entry = ctk.CTkEntry(call_frame, width=120)
        self.target_ip_entry.insert(0, "127.0.0.1")
        self.target_ip_entry.grid(row=0, column=1, padx=5)

        ctk.CTkLabel(call_frame, text="Target RTSP Port:").grid(row=1, column=0, padx=5)
        self.target_rtsp_entry = ctk.CTkEntry(call_frame, width=60)
        self.target_rtsp_entry.insert(0, "5541")
        self.target_rtsp_entry.grid(row=1, column=1, padx=5)
        
        self.call_btn = ctk.CTkButton(call_frame, text="Call", command=self.make_call, fg_color="green", width=80)
        self.call_btn.grid(row=0, column=2, padx=5)
        
        self.hangup_btn = ctk.CTkButton(call_frame, text="Hang Up", command=self.hang_up, fg_color="red", width=80, state="disabled")
        self.hangup_btn.grid(row=1, column=2, padx=5)

        # Status Label
        self.status_label = ctk.CTkLabel(self, text="Waiting to start server...", text_color="gray")
        self.status_label.pack(pady=5)

        # Video Panel
        video_frame = ctk.CTkFrame(self, fg_color="transparent")
        video_frame.pack(expand=True, fill="both", padx=10, pady=10)
        
        video_frame.grid_columnconfigure(0, weight=1)
        video_frame.grid_columnconfigure(1, weight=1)
        
        # Local Video
        local_container = ctk.CTkFrame(video_frame)
        local_container.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(local_container, text="You", font=("Arial", 16, "bold")).pack(pady=5)
        self.local_video_label = ctk.CTkLabel(local_container, text="")
        self.local_video_label.pack(expand=True)
        
        # Remote Video
        remote_container = ctk.CTkFrame(video_frame)
        remote_container.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        ctk.CTkLabel(remote_container, text="Remote", font=("Arial", 16, "bold")).pack(pady=5)
        self.remote_video_label = ctk.CTkLabel(remote_container, text="")
        self.remote_video_label.pack(expand=True)

    def start_server(self):
        try:
            port = int(self.my_rtsp_port_entry.get())
            self.server = RtspServer(port, on_client_connected=self.on_incoming_call)
            self.server.start()
            self.start_server_btn.configure(state="disabled", text="Server Running")
            self.my_rtsp_port_entry.configure(state="disabled")
            self.update_status(f"Listening for calls on port {port}...")
        except Exception as e:
            self.update_status(f"Server Error: {e}")

    def on_incoming_call(self, peer_ip):
        self.update_status(f"Incoming call from {peer_ip}")

    def make_call(self):
        if not self.server:
            self.update_status("Please start your server first!")
            return
            
        target_ip = self.target_ip_entry.get()
        target_port = int(self.target_rtsp_entry.get())
        my_rtp_port = int(self.my_rtp_port_entry.get())
        
        self.client = RtspClient(
            target_ip, target_port, my_rtp_port,
            on_frame_received=self.render_remote_frame,
            on_status_change=self.update_status
        )
        
        if self.client.connect():
            self.call_btn.configure(state="disabled")
            self.hangup_btn.configure(state="normal")

    def hang_up(self):
        if self.client:
            self.client.teardown()
            self.client = None
        self.remote_video_label.configure(image="")
        self.call_btn.configure(state="normal")
        self.hangup_btn.configure(state="disabled")

    def update_status(self, msg):
        self.status_label.configure(text=msg)

    def update_local_preview(self):
        """Continuously pulls frames from the shared webcam and renders to GUI."""
        rgb_frame = self.shared_cam.get_latest_rgb()
        if rgb_frame is not None:
            # Resize for UI
            img = Image.fromarray(rgb_frame)
            img.thumbnail((400, 300))
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
            self.local_video_label.configure(image=ctk_img)
            self.local_video_label.image = ctk_img
            
        self.after(30, self.update_local_preview)

    def render_remote_frame(self, jpeg_bytes):
        """Callback from RtspClient to render incoming RTP frames."""
        try:
            image = Image.open(io.BytesIO(jpeg_bytes))
            image.thumbnail((400, 300))
            ctk_img = ctk.CTkImage(light_image=image, dark_image=image, size=image.size)
            self.remote_video_label.configure(image=ctk_img)
            self.remote_video_label.image = ctk_img
        except Exception as e:
            print("Render error:", e)

    def destroy(self):
        if self.client:
            self.client.teardown()
        if self.server:
            self.server.stop()
        self.shared_cam.close()
        super().destroy()

if __name__ == "__main__":
    app = VideoChatApp()
    app.protocol("WM_DELETE_WINDOW", app.destroy)
    app.mainloop()
