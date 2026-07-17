'use client';

import { useEffect, useRef, useState } from 'react';
import Peer, { Instance } from 'simple-peer';
import { initSocket } from '@/lib/socket';

export default function VideoStream({ roomId, isInitiator = false }: { roomId: string, isInitiator?: boolean }) {
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const myVideo = useRef<HTMLVideoElement>(null);
  const userVideo = useRef<HTMLVideoElement>(null);
  const peerRef = useRef<Instance | null>(null);

  useEffect(() => {
    // CRITICAL: This must be a closure variable, NOT a ref.
    // useRef persists across Strict Mode remounts, so Mount #2 would
    // overwrite the cleanup flag set by Mount #1's teardown, causing
    // Mount #1's async getUserMedia to think it's still alive.
    let cleanedUp = false;
    let localStream: MediaStream | null = null;
    
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setError('Camera access is not supported in this browser. You must use HTTPS or localhost to access the camera.');
      return;
    }

    const socket = initSocket();

    // Remove any stale listeners from a previous mount
    socket.off('user-connected');
    socket.off('signal');
    socket.off('user-disconnected');

    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      .then((mediaStream) => {
        // If this effect was cleaned up while awaiting camera, stop immediately
        if (cleanedUp) {
          mediaStream.getTracks().forEach(track => track.stop());
          return;
        }

        localStream = mediaStream;
        if (myVideo.current) {
          myVideo.current.srcObject = mediaStream;
        }

        // --- Socket event handlers ---

        socket.on('user-connected', (userId: string) => {
          if (cleanedUp) return;
          console.log('[WebRTC] Remote user joined, creating offer for:', userId);
          
          if (peerRef.current) {
            peerRef.current.destroy();
            peerRef.current = null;
          }

          const peer = new Peer({
            initiator: true,
            trickle: false,
            stream: mediaStream,
          });

          peer.on('signal', (signalData) => {
            if (cleanedUp) return;
            console.log('[WebRTC] Sending offer to:', userId);
            socket.emit('signal', { to: userId, signal: signalData });
          });

          peer.on('stream', (remoteStream) => {
            console.log('[WebRTC] Received remote stream!');
            if (userVideo.current) {
              userVideo.current.srcObject = remoteStream;
            }
            if (!cleanedUp) setConnected(true);
          });

          peer.on('connect', () => console.log('[WebRTC] Connected!'));
          peer.on('error', (err) => console.error('[WebRTC] Error:', err.message));
          peer.on('close', () => console.log('[WebRTC] Closed'));

          peerRef.current = peer;
        });

        socket.on('signal', (data: { from: string; signal: any }) => {
          if (cleanedUp) return;
          const type = data.signal?.type;
          console.log('[WebRTC] Received signal:', type, 'from:', data.from);

          if (type === 'offer') {
            // We are the non-initiator: create a peer to answer
            if (peerRef.current) {
              peerRef.current.destroy();
              peerRef.current = null;
            }

            const peer = new Peer({
              initiator: false,
              trickle: false,
              stream: mediaStream,
            });

            peer.on('signal', (signalData) => {
              if (cleanedUp) return;
              console.log('[WebRTC] Sending answer to:', data.from);
              socket.emit('signal', { to: data.from, signal: signalData });
            });

            peer.on('stream', (remoteStream) => {
              console.log('[WebRTC] Received remote stream!');
              if (userVideo.current) {
                userVideo.current.srcObject = remoteStream;
              }
              if (!cleanedUp) setConnected(true);
            });

            peer.on('connect', () => console.log('[WebRTC] Connected!'));
            peer.on('error', (err) => console.error('[WebRTC] Error:', err.message));
            peer.on('close', () => console.log('[WebRTC] Closed'));

            peerRef.current = peer;
            peer.signal(data.signal);

          } else if (type === 'answer') {
            // We are the initiator: feed the answer into our existing peer
            if (peerRef.current && !peerRef.current.destroyed) {
              console.log('[WebRTC] Processing answer');
              peerRef.current.signal(data.signal);
            } else {
              console.warn('[WebRTC] Got answer but no initiator peer exists');
            }
          }
        });

        socket.on('user-disconnected', () => {
          if (cleanedUp) return;
          console.log('[WebRTC] Remote user disconnected');
          setConnected(false);
          if (userVideo.current) {
            userVideo.current.srcObject = null;
          }
          if (peerRef.current) {
            peerRef.current.destroy();
            peerRef.current = null;
          }
        });

        // Join the room AFTER all listeners are ready
        socket.emit('join-room', roomId);
      })
      .catch((err) => {
        console.error('Failed to get local stream', err);
        if (!cleanedUp) {
          setError('Could not access camera or microphone. Please ensure permissions are granted.');
        }
      });

    return () => {
      cleanedUp = true;
      
      socket.off('user-connected');
      socket.off('signal');
      socket.off('user-disconnected');
      
      if (peerRef.current) {
        peerRef.current.destroy();
        peerRef.current = null;
      }
      
      if (localStream) {
        localStream.getTracks().forEach(track => track.stop());
        localStream = null;
      }
    };
  }, [roomId]);

  return (
    <div className="w-full flex flex-col md:flex-row gap-4 p-4">
      <div className="flex-1 bg-gray-900 rounded-2xl overflow-hidden relative shadow-xl aspect-video border-2 border-gray-800">
        <video 
          playsInline 
          muted 
          ref={myVideo} 
          autoPlay 
          className="w-full h-full object-cover"
        />
        <div className="absolute bottom-4 left-4 bg-black/50 text-white px-3 py-1 rounded-full text-sm backdrop-blur-sm">
          You
        </div>
      </div>

      <div className="flex-1 bg-gray-900 rounded-2xl overflow-hidden relative shadow-xl aspect-video border-2 border-gray-800">
        <video 
          playsInline 
          ref={userVideo} 
          autoPlay 
          className={`w-full h-full object-cover ${connected ? 'block' : 'hidden'}`}
        />
        {!connected && (
          <div className="w-full h-full flex items-center justify-center text-gray-500 flex-col absolute inset-0 z-10 bg-gray-900">
            <div className="w-12 h-12 mb-4 rounded-full border-4 border-gray-600 border-t-blue-500 animate-spin" />
            <p>Waiting for connection...</p>
          </div>
        )}
        <div className="absolute bottom-4 left-4 bg-black/50 text-white px-3 py-1 rounded-full text-sm backdrop-blur-sm">
          Remote
        </div>
      </div>
      
      {error && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-red-500 text-white px-4 py-2 rounded shadow-lg">
          {error}
        </div>
      )}
    </div>
  );
}
