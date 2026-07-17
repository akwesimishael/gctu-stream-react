'use client';

import { useEffect, useState } from 'react';
import QrDisplay from '@/components/QrDisplay';
import VideoStream from '@/components/VideoStream';

export default function Home() {
  const [roomId, setRoomId] = useState('');

  useEffect(() => {
    // Generate a random room ID on mount
    const id = Math.random().toString(36).substring(2, 10);
    setRoomId(id);
  }, []);

  if (!roomId) return null;

  return (
    <main className="min-h-screen bg-gray-50 flex flex-col items-center p-8 font-sans">
      <div className="w-full max-w-5xl">
        <header className="mb-8 text-center">
          <h1 className="text-4xl font-extrabold text-gray-900 tracking-tight">Local Stream Platform</h1>
          <p className="text-gray-500 mt-2">Scan the QR code below to connect your device</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-1 flex flex-col items-center">
            <QrDisplay roomId={roomId} />
          </div>
          
          <div className="lg:col-span-2">
            <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-100">
              <h2 className="text-xl font-semibold mb-4 text-gray-800">Live Stream</h2>
              <VideoStream roomId={roomId} isInitiator={true} />
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
