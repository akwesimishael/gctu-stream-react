'use client';

import { useEffect, useRef, useState } from 'react';
import Peer, { Instance } from 'simple-peer';
import { initSocket } from '@/lib/socket';

export default function VideoStream({ roomId, isInitiator = false }: { roomId: string, isInitiator?: boolean }) {
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const myVideo = useRef<HTMLVideoElement>(null);
  const userVideo = useRef<HTMLVideoElement>(null);
  const peerRef = useRef<Instance | null>(null);

  useEffect(() => {
    let currentStream: MediaStream | null = null;
    
    // Get local video stream
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      .then((mediaStream) => {
        currentStream = mediaStream;
        setStream(mediaStream);
        if (myVideo.current) {
          myVideo.current.srcObject = mediaStream;
        }

        const socket = initSocket();
        socket.emit('join-room', roomId);

        // When another user connects to the room
        socket.on('user-connected', (userId) => {
          console.log('User connected:', userId);
          // Only the user already in the room (initiator) creates the initial offer
          const peer = new Peer({
            initiator: true,
            trickle: false,
            stream: mediaStream,
          });

          peer.on('signal', (data) => {
            socket.emit('offer', { to: userId, signal: data });
          });

          peer.on('stream', (userStream) => {
            if (userVideo.current) {
              userVideo.current.srcObject = userStream;
            }
          });

          socket.on('answer', (data) => {
            peer.signal(data.signal);
            setConnected(true);
          });

          peerRef.current = peer;
        });

        // When receiving an offer
        socket.on('offer', (data) => {
          const peer = new Peer({
            initiator: false,
            trickle: false,
            stream: mediaStream,
          });

          peer.on('signal', (signalData) => {
            socket.emit('answer', { to: data.from, signal: signalData });
          });

          peer.on('stream', (userStream) => {
            if (userVideo.current) {
              userVideo.current.srcObject = userStream;
            }
          });

          peer.signal(data.signal);
          setConnected(true);
          peerRef.current = peer;
        });

        socket.on('user-disconnected', () => {
          setConnected(false);
          if (userVideo.current) {
            userVideo.current.srcObject = null;
          }
          if (peerRef.current) {
            peerRef.current.destroy();
            peerRef.current = null;
          }
        });

      })
      .catch((err) => {
        console.error('Failed to get local stream', err);
        setError('Could not access camera or microphone. Please ensure permissions are granted.');
      });

    return () => {
      // Cleanup
      if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
      }
      if (peerRef.current) {
        peerRef.current.destroy();
      }
      const socket = initSocket();
      socket.off('user-connected');
      socket.off('offer');
      socket.off('answer');
      socket.off('user-disconnected');
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
        {connected ? (
          <video 
            playsInline 
            ref={userVideo} 
            autoPlay 
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-500 flex-col">
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
