'use client';

import { use, useEffect } from 'react';
import VideoStream from '@/components/VideoStream';

export default function StreamPage({ params }: { params: Promise<{ roomId: string }> }) {
  const { roomId } = use(params);

  return (
    <main className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4 font-sans text-white">
      <div className="w-full max-w-4xl bg-gray-800 p-6 rounded-2xl shadow-2xl border border-gray-700">
        <h1 className="text-2xl font-bold mb-6 text-center">Connected to Room: {roomId}</h1>
        <VideoStream roomId={roomId} isInitiator={false} />
      </div>
    </main>
  );
}
